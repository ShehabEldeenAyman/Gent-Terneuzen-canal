"""Reusable, observable stages for the canal data pipelines.

The functions in this module deliberately return metadata instead of only
printing.  They are used by the pipeline playground API as well as by the
small command-line wrappers in this directory.
"""

from contextlib import contextmanager
from pathlib import Path
import os
import subprocess
import sys
import time


ROOT_DIR = Path(__file__).resolve().parents[1]
PIPELINE_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
RML_DIR = ROOT_DIR / "RML_mapping"
SHACL_DIR = ROOT_DIR / "SHACL"
RULES_DIR = ROOT_DIR / "N3rules"


def setup_environment():
    """Make pipeline collaborators importable without the forecasting server."""
    for directory in (
        ROOT_DIR / "data_fetch",
        ROOT_DIR / "pre_processing",
        ROOT_DIR / "triple_store_ingestion",
        ROOT_DIR / "RDF2TSS_V2",
        ROOT_DIR / "RDF2LDES",
        ROOT_DIR / "RML_generator",
        ROOT_DIR / "automating_aligments",
        ROOT_DIR / "RDF2LDES",
        SHACL_DIR,
    ):
        path = str(directory)
        if path not in sys.path:
            sys.path.insert(0, path)


@contextmanager
def pipeline_working_directory():
    """Support legacy collaborators that resolve paths relative to pipeline/."""
    previous = Path.cwd()
    os.chdir(PIPELINE_DIR)
    try:
        yield
    finally:
        os.chdir(previous)


def _run(command, label):
    started = time.perf_counter()
    try:
        completed = subprocess.run(command, capture_output=True, text=True, check=True)
    except FileNotFoundError as error:
        raise RuntimeError(f"{label} cannot start: {error}") from error
    except subprocess.CalledProcessError as error:
        detail = error.stderr or error.stdout or str(error)
        raise RuntimeError(f"{label} failed: {detail.strip()}") from error
    return {
        "message": f"{label} completed successfully.",
        "duration_seconds": round(time.perf_counter() - started, 2),
        "command_output": (completed.stdout + completed.stderr).strip(),
    }


def step_1_fetch_data(start_date, end_date, timeseriesgroup_ids, parameter_name):
    setup_environment()
    import fetch
    fetch.fetch_timeseries(start_date, end_date, timeseriesgroup_ids, parameter_name)
    return {"message": f"Fetched {parameter_name} measurements.", "artifacts": [data_path(f"{parameter_name}.csv")]}


def step_2_preprocess(parameter_name):
    setup_environment()
    import preprocess
    import preprocess2
    preprocess.preprocess(parameter_name)
    preprocess2.preprocess(parameter_name)
    return {"message": f"Prepared {parameter_name} CSV data.", "artifacts": [data_path(f"{parameter_name}.csv")]}


def step_1_pre_process_waterlink(input_path=None, output_path=None):
    setup_environment()
    import preprocess_waterlink
    input_path = Path(input_path) if input_path else DATA_DIR / "water-link" / "data.xlsx"
    output_path = Path(output_path) if output_path else DATA_DIR / "water_link.csv"
    preprocess_waterlink.clean_result_sheet(str(input_path), str(output_path))
    return {"message": "Prepared Water-Link workbook data.", "artifacts": [output_path]}


def _rml_mapping(parameter_name, generator_type):
    """Generate an RML mapping with the selected generator and run RMLMapper."""
    setup_environment()
    generator = __import__(generator_type)
    generator.generate_timeseries_mapping(parameter_name)
    mapping = RML_DIR / f"{parameter_name}.rml.ttl"
    output = DATA_DIR / f"{parameter_name}.ttl"
    result = _run(["java", "-jar", "rmlmapper.jar", "-m", str(mapping), "-o", str(output), "-s", "turtle"], "RML mapping")
    result["artifacts"] = [mapping, output]
    return result


def step_3_rml_mapping(parameter_name, generator_type="RML_generator"):
    return _rml_mapping(parameter_name, generator_type)


def step_2_rml_mapping_waterlink(parameter_name="water_link"):
    return _rml_mapping(parameter_name, "RML_generator_waterlink")


def step_shacl_validate(data_path, shape_path, report_path):
    setup_environment()
    import SHACL_validate
    result = SHACL_validate.validate_shacl(str(data_path), str(shape_path), str(report_path))
    result["artifacts"] = [Path(report_path)]
    return result


def step_3_5_automating_alignments(data_path, new_unit):
    setup_environment()
    import automated_alignments
    result = automated_alignments.transform_unit_optimized(str(data_path), new_unit)
    return {"message": result or "Aligned observation units to the canonical unit.", "artifacts": [Path(data_path)]}


def step_5_rdf2tss(input_path, output_path, observed_parameter="unknown", overwrite=True):
    setup_environment()
    import RDF2TSS_V2
    original_graph = RDF2TSS_V2.load_graph(str(input_path))
    sensor_set = RDF2TSS_V2.create_sensor_set(original_graph)
    tss_graph = RDF2TSS_V2.create_tss(sensor_set, original_graph, observed_parameter)
    RDF2TSS_V2.save_graph(str(output_path), tss_graph, overwrite)
    return {"message": f"Created TSS for {len(sensor_set)} sensor(s).", "artifacts": [Path(output_path)]}


def step_5_5_reasoner(data_path, rule_path):
    """Run EYE and save inferred triples next to the source RDF file."""
    output_path = Path(data_path).with_name(f"{Path(data_path).stem}_inferred.ttl")
    result = _run(["eye", str(data_path), str(rule_path), "--nope", "--pass-only-new"], "N3 reasoning")
    output_path.write_text(result["command_output"] + "\n", encoding="utf-8")
    result["artifacts"] = [output_path]
    return result


def step_4_ingest_triplestore(ttl_timeseries, graph_uri, delete_existing=True):
    setup_environment()
    import ingest
    if delete_existing and not ingest.delete_graph(graph_uri):
        raise RuntimeError("Fuseki graph deletion failed.")
    if not ingest.upload_graph(str(ttl_timeseries), graph_uri):
        raise RuntimeError("Fuseki upload failed. Check the data endpoint and server logs.")
    return {"message": f"Uploaded data to Fuseki graph {graph_uri}."}


def ldes_artifacts(directory_input, limit=24):
    """Return a useful, bounded preview of a generated LDES tree.

    A full run can create hundreds of daily ``readings.trig`` fragments.  The
    dashboard needs the TREE indexes plus a recent sample, rather than a huge
    response containing every fragment.
    """
    output_directory = Path(directory_input).resolve()
    if not output_directory.is_dir():
        return []

    trig_files = list(output_directory.rglob("*.trig"))
    indexes = sorted(
        (path for path in trig_files if path.name != "readings.trig"),
        key=lambda path: (len(path.relative_to(output_directory).parts), path.as_posix()),
    )
    fragments = sorted(
        (path for path in trig_files if path.name == "readings.trig"),
        key=lambda path: path.as_posix(),
        reverse=True,
    )
    index_limit = min(8, limit)
    return (indexes[:index_limit] + fragments[: max(0, limit - index_limit)])[:limit]


def step_6_RDF2LDES(property_name, source_ttl, directory_input, base_path_input):
    setup_environment()
    import RDFTSS2LDES

    RDFTSS2LDES.set_property(property_name, directory_input, base_path_input)
    raw_graph = RDFTSS2LDES.load_graph(str(source_ttl))
    sparql_results = RDFTSS2LDES.process_graph(raw_graph)
    RDFTSS2LDES.divide_data(sparql_results)
    RDFTSS2LDES.delete_log()
    RDFTSS2LDES.delete_ldes_files()
    RDFTSS2LDES.create_ldes_files()

    output_directory = Path(directory_input).resolve()
    generated = list(output_directory.rglob("*.trig")) if output_directory.is_dir() else []
    index_count = sum(path.name != "readings.trig" for path in generated)
    fragment_count = sum(path.name == "readings.trig" for path in generated)
    return {
        "message": f"Created an LDES with {index_count} TREE index file(s) and {fragment_count} daily fragment(s).",
        "artifacts": ldes_artifacts(output_directory),
    }


# Compatibility alias for scripts that still use the former name.
step_4_ingest_virtuoso = step_4_ingest_triplestore


def data_path(name):
    return DATA_DIR / name
