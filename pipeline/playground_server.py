"""API for the interactive Canal Data Operations dashboard.

Run with: uvicorn pipeline.playground_server:app --reload --port 8000
"""

import ast
import csv
import mimetypes
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from threading import Lock
from time import perf_counter

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from rdflib import URIRef

from pipeline import pipeline_core as core
from triple_store_ingestion import ingest


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
RUN_LOCK = Lock()
GRAPH_URI = "http://example.com/Gent-Terneuzen"

WATERINFO = {
    "parameter": "conductivity",
    "sensor_ids": ["289435042", "289423042", "289429042", "289441042"],
    "start": "2025-01-01T00:00:00Z",
    "end": "2026-03-31T23:59:59Z",
}

STAGES = {
    "water-link": [
        ("prepare", "Prepare workbook", "Clean the Water-Link source workbook into a usable CSV.", "step_1_pre_process_waterlink", None),
        ("map", "Map to RDF", "Generate the RML mapping and transform CSV records into Turtle RDF.", "step_2_rml_mapping_waterlink", None),
        ("validate-input", "Validate source", "Check the source graph against the input SHACL contract.", "step_shacl_validate", "SHACL_in"),
        ("align", "Normalize units", "Convert observations to the canonical milliSiemens per centimetre unit.", "step_3_5_automating_alignments", None),
        ("validate-output", "Validate normalized graph", "Confirm that the normalized graph meets the output SHACL contract.", "step_shacl_validate", "SHACL_out"),
        ("tss", "Create time-series snippets", "Create TSS resources from the RDF observations.", "step_5_rdf2tss", None),
        ("reason", "Apply N3 rules", "Materialize quality annotations and inferred triples.", "step_5_5_reasoner", None),
        ("ingest", "Publish to Fuseki", "Upload the RDF graph to Apache Jena Fuseki.", "step_4_ingest_virtuoso", None),
    ],
    "waterinfo-conductivity": [
        ("fetch", "Fetch measurements", "Download the configured Waterinfo conductivity series.", "step_1_fetch_data", None),
        ("prepare", "Prepare CSV", "Add Unix timestamps and normalize date values.", "step_2_preprocess", None),
        ("map", "Map to RDF", "Generate RML and transform CSV measurements into Turtle RDF.", "step_3_rml_mapping", None),
        ("validate-input", "Validate source", "Check the source graph against the input SHACL contract.", "step_shacl_validate", "SHACL_in"),
        ("align", "Normalize units", "Convert observations to the canonical milliSiemens per centimetre unit.", "step_3_5_automating_alignments", None),
        ("validate-output", "Validate normalized graph", "Confirm that the normalized graph meets the output SHACL contract.", "step_shacl_validate", "SHACL_out"),
        ("tss", "Create time-series snippets", "Create TSS resources from the RDF observations.", "step_5_rdf2tss", None),
        ("ingest", "Publish to Fuseki", "Upload the RDF graph to Apache Jena Fuseki.", "step_4_ingest_virtuoso", None),
    ],
}
PIPELINE_FILES = {
    "water-link": ROOT_DIR / "pipeline" / "pipeline_waterlink.py",
    "waterinfo-conductivity": ROOT_DIR / "pipeline" / "pipeline_waterinfo.py",
}
results = {}

app = FastAPI(title="Canal Data Operations API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class SparqlRequest(BaseModel):
    query: str = Field(min_length=1, max_length=50_000)


def relative(path):
    return str(Path(path).resolve().relative_to(ROOT_DIR)).replace("\\", "/")


def artifact(path):
    path = Path(path)
    return {
        "path": relative(path),
        "exists": path.exists(),
        "size": path.stat().st_size if path.exists() else 0,
        "updated_at": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat() if path.exists() else None,
    }


def active_calls(use_case):
    """Read the actual pipeline code: comments never appear in the AST."""
    source = PIPELINE_FILES[use_case].read_text(encoding="utf-8")
    tree = ast.parse(source)
    calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == "core":
            calls.append((node.func.attr, ast.get_source_segment(source, node) or ""))
    return calls


def expected_artifacts(use_case, stage_id):
    parameter = "water_link" if use_case == "water-link" else WATERINFO["parameter"]
    tss_name = "waterlink_tss.ttl" if use_case == "water-link" else f"{parameter}_tss.ttl"
    files = {
        "prepare": [DATA_DIR / f"{parameter}.csv"],
        "map": [ROOT_DIR / "RML_mapping" / f"{parameter}.rml.ttl", DATA_DIR / f"{parameter}.ttl"],
        "validate-input": [DATA_DIR / f"{parameter}_shacl_in_report.txt"],
        "align": [DATA_DIR / f"{parameter}.ttl"],
        "validate-output": [DATA_DIR / f"{parameter}_shacl_out_report.txt"],
        "tss": [DATA_DIR / tss_name],
        "reason": [DATA_DIR / f"{parameter}_inferred.ttl"],
        "ingest": [],
    }
    return [artifact(path) for path in files.get(stage_id, [])]


def stage_catalog(use_case):
    calls = active_calls(use_case)
    catalog = []
    for stage_id, title, description, function_name, marker in STAGES[use_case]:
        enabled = any(name == function_name and (marker is None or marker in expression) for name, expression in calls)
        catalog.append({
            "id": stage_id, "title": title, "description": description, "available": enabled,
            "unavailable_reason": None if enabled else "This stage is currently commented out or absent from the pipeline source.",
            "artifacts": expected_artifacts(use_case, stage_id),
        })
    return catalog


def stage_result(use_case, stage_id):
    if use_case == "water-link":
        rdf = DATA_DIR / "water_link.ttl"
        actions = {
            "prepare": lambda: core.step_1_pre_process_waterlink(),
            "map": lambda: core.step_2_rml_mapping_waterlink(),
            "validate-input": lambda: core.step_shacl_validate(rdf, ROOT_DIR / "SHACL/SHACL_in.ttl", DATA_DIR / "water_link_shacl_in_report.txt"),
            "align": lambda: core.step_3_5_automating_alignments(rdf, URIRef("http://qudt.org/vocab/unit/MilliS-PER-CentiM")),
            "validate-output": lambda: core.step_shacl_validate(rdf, ROOT_DIR / "SHACL/SHACL_out.ttl", DATA_DIR / "water_link_shacl_out_report.txt"),
            "tss": lambda: core.step_5_rdf2tss(rdf, DATA_DIR / "water_link_tss.ttl", "Data/conductivity"),
            "reason": lambda: core.step_5_5_reasoner(rdf, ROOT_DIR / "N3rules/rules.n3"),
            "ingest": lambda: core.step_4_ingest_triplestore(rdf, GRAPH_URI, delete_existing=False),
        }
    else:
        parameter = WATERINFO["parameter"]
        rdf = DATA_DIR / f"{parameter}.ttl"
        actions = {
            "fetch": lambda: core.step_1_fetch_data(WATERINFO["start"], WATERINFO["end"], WATERINFO["sensor_ids"], parameter),
            "prepare": lambda: core.step_2_preprocess(parameter),
            "map": lambda: core.step_3_rml_mapping(parameter),
            "validate-input": lambda: core.step_shacl_validate(rdf, ROOT_DIR / "SHACL/SHACL_in.ttl", DATA_DIR / f"{parameter}_shacl_in_report.txt"),
            "align": lambda: core.step_3_5_automating_alignments(rdf, URIRef("http://qudt.org/vocab/unit/MilliS-PER-CentiM")),
            "validate-output": lambda: core.step_shacl_validate(rdf, ROOT_DIR / "SHACL/SHACL_out.ttl", DATA_DIR / f"{parameter}_shacl_out_report.txt"),
            "tss": lambda: core.step_5_rdf2tss(rdf, DATA_DIR / f"{parameter}_tss.ttl", f"Data/{parameter}"),
            "ingest": lambda: core.step_4_ingest_triplestore(rdf, GRAPH_URI, delete_existing=False),
        }
    return actions[stage_id]()


def artifact_summary(path):
    target = (ROOT_DIR / path).resolve()
    if ROOT_DIR not in target.parents or not target.is_file():
        raise HTTPException(404, "Artifact not found")
    response = {**artifact(target), "kind": target.suffix.lower().lstrip("."), "mime_type": mimetypes.guess_type(target.name)[0] or "text/plain"}
    if target.suffix.lower() == ".csv":
        with target.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            reader = csv.DictReader(handle)
            response["columns"] = reader.fieldnames or []
            response["rows"] = [row for _, row in zip(range(30), reader)]
        return response
    text = target.read_text(encoding="utf-8", errors="replace")
    response["text"] = text[:30_000]
    response["truncated"] = len(text) > len(response["text"])
    return response


@app.get("/api/use-cases")
def list_use_cases():
    return [
        {
            "id": use_case,
            "title": "Water-Link conductivity" if use_case == "water-link" else "Waterinfo conductivity",
            "description": "Workbook-to-Fuseki semantic pipeline." if use_case == "water-link" else "Waterinfo-to-Fuseki semantic pipeline.",
            "stages": stage_catalog(use_case),
            "results": results.get(use_case, {}),
        }
        for use_case in STAGES
    ]


@app.get("/api/fuseki/status")
def fuseki_status():
    try:
        response = requests.get(ingest.get_query_url(), params={"query": "ASK {}"}, headers={"Accept": "application/sparql-results+json"}, timeout=5)
        return {"connected": response.ok, "data_endpoint": ingest.FUSEKI_DATA_URL, "query_endpoint": ingest.get_query_url(), "status_code": response.status_code}
    except requests.RequestException as error:
        return {"connected": False, "data_endpoint": ingest.FUSEKI_DATA_URL, "query_endpoint": ingest.get_query_url(), "detail": str(error)}


@app.post("/api/use-cases/{use_case}/stages/{stage_id}")
def run_stage(use_case: str, stage_id: str):
    if use_case not in STAGES:
        raise HTTPException(404, "Unknown use case")
    stage = next((item for item in stage_catalog(use_case) if item["id"] == stage_id), None)
    if not stage:
        raise HTTPException(404, "Unknown pipeline stage")
    if not stage["available"]:
        payload = {"status": "unavailable", "message": stage["unavailable_reason"], "log": "", "duration_seconds": 0, "artifacts": []}
        results.setdefault(use_case, {})[stage_id] = payload
        return payload
    stream = StringIO()
    started = perf_counter()
    try:
        with RUN_LOCK, core.pipeline_working_directory(), redirect_stdout(stream), redirect_stderr(stream):
            outcome = stage_result(use_case, stage_id)
        payload = {"status": "success", "message": outcome.get("message", "Stage completed."), "log": stream.getvalue(), "duration_seconds": round(perf_counter() - started, 2), "artifacts": [artifact(path) for path in outcome.get("artifacts", [])]}
    except Exception as error:
        payload = {"status": "error", "message": str(error), "log": stream.getvalue(), "duration_seconds": round(perf_counter() - started, 2), "artifacts": []}
    results.setdefault(use_case, {})[stage_id] = payload
    return payload


@app.get("/api/artifacts/{path:path}/summary")
def read_artifact_summary(path: str):
    return artifact_summary(path)


@app.get("/api/artifacts/{path:path}", response_class=PlainTextResponse)
def read_artifact(path: str):
    summary = artifact_summary(path)
    if "text" in summary:
        return summary["text"]
    raise HTTPException(415, "Use the artifact summary endpoint for CSV previews")


@app.post("/api/sparql")
def sparql_query(request: SparqlRequest):
    try:
        response = requests.post(ingest.get_query_url(), data={"query": request.query}, headers={"Accept": "application/sparql-results+json"}, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as error:
        raise HTTPException(502, f"Fuseki query failed: {error}") from error
    except ValueError as error:
        raise HTTPException(502, "Fuseki did not return SPARQL JSON results.") from error
