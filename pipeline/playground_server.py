"""FastAPI server for running and inspecting named pipeline stages.

Run from the repository root with:
    uvicorn pipeline.playground_server:app --reload --port 8000
"""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from threading import Lock
from time import perf_counter

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from rdflib import URIRef

from pipeline import pipeline_core as core


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
RUN_LOCK = Lock()

USE_CASES = {
    "water-link": {
        "title": "Water-Link conductivity",
        "description": "Clean the supplied workbook, map it to RDF, validate and align units, then create TSS and inferred RDF.",
        "stages": [
            ("prepare", "Prepare workbook", "Clean the Water-Link Excel result sheet into a CSV."),
            ("map", "Map to RDF", "Generate RML and transform the CSV into Turtle RDF."),
            ("validate-input", "Validate input", "Check the source RDF against the MicroS/cm SHACL shape."),
            ("align", "Align units", "Convert observations to milliSiemens per centimetre."),
            ("validate-output", "Validate output", "Check the normalized RDF against the canonical SHACL shape."),
            ("tss", "Create TSS", "Create Time Series Snippets from the RDF observations."),
            ("reason", "Run N3 rules", "Generate inferred triples and quality annotations."),
            ("ingest", "Ingest to Virtuoso", "Upload the normalized RDF to the configured named graph."),
        ],
    },
    "waterinfo-conductivity": {
        "title": "Waterinfo conductivity",
        "description": "Fetch conductivity measurements, then apply the same semantic quality pipeline.",
        "stages": [
            ("fetch", "Fetch measurements", "Download the configured Waterinfo sensor series."),
            ("prepare", "Prepare CSV", "Add Unix timestamps and normalize date formatting."),
            ("map", "Map to RDF", "Generate RML and transform CSV measurements into Turtle RDF."),
            ("validate-input", "Validate input", "Check source RDF against the MicroS/cm SHACL shape."),
            ("align", "Align units", "Convert observations to milliSiemens per centimetre."),
            ("validate-output", "Validate output", "Check normalized RDF against the canonical SHACL shape."),
            ("tss", "Create TSS", "Create Time Series Snippets from the RDF observations."),
            ("ingest", "Ingest to Virtuoso", "Upload normalized RDF to the configured named graph."),
        ],
    },
}

WATERINFO = {
    "parameter": "conductivity",
    "sensor_ids": ["289435042", "289423042", "289429042", "289441042"],
    "start": "2021-01-01T00:00:00Z",
    "end": "2026-03-31T23:59:59Z",
}
GRAPH_URI = "http://example.com/Gent-Terneuzen"
results = {}

app = FastAPI(title="Canal Pipeline Playground")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def relative(path):
    return str(Path(path).resolve().relative_to(ROOT_DIR)).replace("\\", "/")


def artifact(path):
    path = Path(path)
    return {"path": relative(path), "exists": path.exists(), "size": path.stat().st_size if path.exists() else 0}


def stage_result(use_case, stage_id):
    if use_case == "water-link":
        rdf = DATA_DIR / "water_link.ttl"
        if stage_id == "prepare":
            return core.step_1_pre_process_waterlink()
        if stage_id == "map":
            return core.step_2_rml_mapping_waterlink()
        if stage_id == "validate-input":
            return core.step_shacl_validate(rdf, ROOT_DIR / "SHACL/SHACL_in.ttl", DATA_DIR / "water_link_shacl_in_report.txt")
        if stage_id == "align":
            return core.step_3_5_automating_alignments(rdf, URIRef("http://qudt.org/vocab/unit/MilliS-PER-CentiM"))
        if stage_id == "validate-output":
            return core.step_shacl_validate(rdf, ROOT_DIR / "SHACL/SHACL_out.ttl", DATA_DIR / "water_link_shacl_out_report.txt")
        if stage_id == "tss":
            return core.step_5_rdf2tss(rdf, DATA_DIR / "water_link_tss.ttl", "Data/conductivity")
        if stage_id == "reason":
            return core.step_5_5_reasoner(rdf, ROOT_DIR / "N3rules/rules.n3")
    if use_case == "waterinfo-conductivity":
        parameter = WATERINFO["parameter"]
        rdf = DATA_DIR / f"{parameter}.ttl"
        if stage_id == "fetch":
            return core.step_1_fetch_data(WATERINFO["start"], WATERINFO["end"], WATERINFO["sensor_ids"], parameter)
        if stage_id == "prepare":
            return core.step_2_preprocess(parameter)
        if stage_id == "map":
            return core.step_3_rml_mapping(parameter)
        if stage_id == "validate-input":
            return core.step_shacl_validate(rdf, ROOT_DIR / "SHACL/SHACL_in.ttl", DATA_DIR / f"{parameter}_shacl_in_report.txt")
        if stage_id == "align":
            return core.step_3_5_automating_alignments(rdf, URIRef("http://qudt.org/vocab/unit/MilliS-PER-CentiM"))
        if stage_id == "validate-output":
            return core.step_shacl_validate(rdf, ROOT_DIR / "SHACL/SHACL_out.ttl", DATA_DIR / f"{parameter}_shacl_out_report.txt")
        if stage_id == "tss":
            return core.step_5_rdf2tss(rdf, DATA_DIR / f"{parameter}_tss.ttl", f"Data/{parameter}")
    if stage_id == "ingest":
        rdf_name = "water_link.ttl" if use_case == "water-link" else "conductivity.ttl"
        return core.step_4_ingest_virtuoso(DATA_DIR / rdf_name, GRAPH_URI, delete_existing=use_case == "water-link")
    raise HTTPException(404, "Unknown pipeline stage")


@app.get("/api/use-cases")
def list_use_cases():
    return [{"id": key, **value, "results": results.get(key, {})} for key, value in USE_CASES.items()]


@app.post("/api/use-cases/{use_case}/stages/{stage_id}")
def run_stage(use_case: str, stage_id: str):
    if use_case not in USE_CASES or stage_id not in {item[0] for item in USE_CASES[use_case]["stages"]}:
        raise HTTPException(404, "Unknown use case or stage")
    stream = StringIO()
    started = perf_counter()
    try:
        with RUN_LOCK, core.pipeline_working_directory(), redirect_stdout(stream), redirect_stderr(stream):
            outcome = stage_result(use_case, stage_id)
        payload = {
            "status": "success",
            "message": outcome.get("message", "Stage completed."),
            "log": stream.getvalue(),
            "duration_seconds": round(perf_counter() - started, 2),
            "artifacts": [artifact(path) for path in outcome.get("artifacts", [])],
        }
    except Exception as error:
        payload = {"status": "error", "message": str(error), "log": stream.getvalue(), "duration_seconds": round(perf_counter() - started, 2), "artifacts": []}
    results.setdefault(use_case, {})[stage_id] = payload
    return payload


@app.get("/api/artifacts/{path:path}", response_class=PlainTextResponse)
def read_artifact(path: str):
    target = (ROOT_DIR / path).resolve()
    if ROOT_DIR not in target.parents or not target.is_file():
        raise HTTPException(404, "Artifact not found")
    if target.suffix.lower() not in {".csv", ".ttl", ".txt", ".n3"}:
        raise HTTPException(415, "This artifact is not previewable as text")
    return target.read_text(encoding="utf-8", errors="replace")[:200_000]
