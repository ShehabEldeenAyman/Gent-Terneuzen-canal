"""Small, read-only Apache Jena Fuseki client for the analytics workspace."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from threading import Lock
from typing import Iterable

import pandas as pd
import requests
from rdflib import URIRef


DEFAULT_GRAPH_URI = os.getenv(
    "ANALYTICS_DEFAULT_GRAPH_URI", "http://example.com/Gent-Terneuzen"
)
CANONICAL_UNIT_URI = "http://qudt.org/vocab/unit/MilliS-PER-CentiM"
MICRO_S_PER_CM = "http://qudt.org/vocab/unit/MicroS-PER-CentiM"


def query_url() -> str:
    """Use the same Fuseki environment convention as triple_store_ingestion."""
    configured = os.getenv("FUSEKI_QUERY_URL")
    if configured:
        return configured
    data_url = os.getenv("FUSEKI_DATA_URL", "http://localhost:3030/dataset/data")
    return data_url.rsplit("/data", 1)[0] + "/query"


def _iri(value: str) -> str:
    if not value or not value.startswith(("http://", "https://", "urn:")):
        raise ValueError(f"Expected an absolute RDF IRI, received: {value!r}")
    return URIRef(value).n3()


def sensor_label(sensor_uri: str) -> str:
    known = {
        "289441042": "Terneuzen",
        "289435042": "Westdorpe",
        "289429042": "Ghent · far",
        "289423042": "Ghent · near",
        "111111111": "Indusii target",
    }
    identifier = sensor_uri.rstrip("/").rsplit("/", 1)[-1]
    return known.get(identifier, identifier or sensor_uri)


class FusekiError(RuntimeError):
    """Raised when Fuseki cannot serve a valid SPARQL result."""


@dataclass
class _CacheEntry:
    created_at: float
    frame: pd.DataFrame


class FusekiClient:
    def __init__(self, endpoint: str | None = None, timeout: int = 60):
        self.endpoint = endpoint or query_url()
        self.timeout = timeout
        self._cache: dict[tuple, _CacheEntry] = {}
        self._lock = Lock()

    def select(self, query: str, timeout: int | None = None) -> dict:
        try:
            response = requests.post(
                self.endpoint,
                data={"query": query},
                headers={"Accept": "application/sparql-results+json"},
                timeout=timeout or self.timeout,
            )
            response.raise_for_status()
            result = response.json()
        except (requests.RequestException, ValueError) as error:
            raise FusekiError(f"Fuseki query failed at {self.endpoint}: {error}") from error
        if "results" not in result and "boolean" not in result:
            raise FusekiError("Fuseki returned a response that is not SPARQL JSON.")
        return result

    def health(self) -> bool:
        try:
            self.select("ASK { ?subject ?predicate ?object }", timeout=4)
            return True
        except FusekiError:
            return False

    def graphs(self) -> list[str]:
        result = self.select(
            "SELECT DISTINCT ?graph WHERE { GRAPH ?graph { ?s ?p ?o } } ORDER BY ?graph"
        )
        return [row["graph"]["value"] for row in result["results"]["bindings"]]

    def sensors(self, graph_uri: str) -> list[dict]:
        graph = _iri(graph_uri)
        query = f"""
PREFIX sosa: <http://www.w3.org/ns/sosa/>
SELECT ?sensor (COUNT(DISTINCT ?observation) AS ?observations)
       (MIN(?time) AS ?firstTime) (MAX(?time) AS ?lastTime)
WHERE {{
  GRAPH {graph} {{
    ?observation a sosa:Observation ;
                 sosa:madeBySensor ?sensor ;
                 sosa:resultTime ?time ;
                 sosa:hasSimpleResult ?result .
  }}
}}
GROUP BY ?sensor
ORDER BY ?sensor
"""
        result = self.select(query)
        sensors = []
        for row in result["results"]["bindings"]:
            uri = row["sensor"]["value"]
            sensors.append(
                {
                    "uri": uri,
                    "label": sensor_label(uri),
                    "observations": int(row.get("observations", {}).get("value", 0)),
                    "first_time": row.get("firstTime", {}).get("value"),
                    "last_time": row.get("lastTime", {}).get("value"),
                }
            )
        return sensors

    def observations(
        self,
        graph_uri: str,
        sensor_uris: Iterable[str],
        limit: int = 50_000,
        cache_seconds: int = 300,
    ) -> pd.DataFrame:
        sensors = tuple(dict.fromkeys(sensor_uris))
        if not sensors:
            raise ValueError("Select at least one sensor.")
        limit = max(100, min(int(limit), 250_000))
        key = (graph_uri, sensors, limit)
        now = time.monotonic()
        with self._lock:
            cached = self._cache.get(key)
            if cached and now - cached.created_at < cache_seconds:
                return cached.frame.copy()

        graph = _iri(graph_uri)
        sensor_values = " ".join(_iri(sensor) for sensor in sensors)
        query = f"""
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX qudt: <http://qudt.org/schema/qudt/>
SELECT ?observation ?sensor ?time
       (GROUP_CONCAT(DISTINCT STR(?result); separator="|") AS ?values)
       (GROUP_CONCAT(DISTINCT STR(?unit); separator="|") AS ?units)
WHERE {{
  GRAPH {graph} {{
    ?observation a sosa:Observation ;
                 sosa:resultTime ?time ;
                 sosa:madeBySensor ?sensor ;
                 sosa:hasSimpleResult ?result .
    OPTIONAL {{ ?observation qudt:hasUnit ?unit }}
    VALUES ?sensor {{ {sensor_values} }}
  }}
}}
GROUP BY ?observation ?sensor ?time
ORDER BY DESC(?time)
LIMIT {limit}
"""
        result = self.select(query)
        grouped_rows = [
            {
                "observation": row["observation"]["value"],
                "sensor": row["sensor"]["value"],
                "time": row["time"]["value"],
                "values": row.get("values", {}).get("value", ""),
                "units": row.get("units", {}).get("value", ""),
            }
            for row in result["results"]["bindings"]
            if all(name in row for name in ("observation", "sensor", "time"))
        ]
        rows, unit_report = normalize_fuseki_observations(grouped_rows)
        frame = pd.DataFrame(
            rows,
            columns=[
                "observation",
                "sensor",
                "time",
                "result",
                "raw_values",
                "source_units",
                "normalization",
            ],
        )
        frame.attrs["unit_report"] = unit_report
        if frame.empty:
            raise FusekiError(
                "No SOSA observations were found for the selected graph and sensors."
            )
        with self._lock:
            self._cache[key] = _CacheEntry(now, frame.copy())
        return frame


def _split_values(value: str) -> list[str]:
    return list(dict.fromkeys(item for item in value.split("|") if item))


def _legacy_pair(values: list[float]) -> bool:
    nonzero = sorted(abs(value) for value in values if abs(value) > 1e-12)
    return len(nonzero) >= 2 and 9_900 <= nonzero[-1] / nonzero[0] <= 10_100


def normalize_fuseki_observations(grouped_rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """Return one canonical mS/cm value per observation.

    The current named graph exposes a recognizable legacy signature: Water-Link
    observations contain both their raw µS/cm value and the old converter's S/m
    value, plus both unit labels. When that signature is present, Waterinfo rows
    from the same graph are also known to be S/m values mislabelled as mS/cm.
    """
    parsed = []
    legacy_graph = False
    for row in grouped_rows:
        values = [float(value) for value in _split_values(row.get("values", ""))]
        units = _split_values(row.get("units", ""))
        if not values:
            continue
        is_legacy_pair = (
            MICRO_S_PER_CM in units
            and CANONICAL_UNIT_URI in units
            and _legacy_pair(values)
        )
        legacy_graph = legacy_graph or is_legacy_pair
        parsed.append((row, values, units, is_legacy_pair))

    normalized = []
    report: dict[str, dict] = {}
    for row, values, units, is_legacy_pair in parsed:
        sensor = row["sensor"]
        if is_legacy_pair:
            # Raw µS/cm is the larger member; /1000 gives mS/cm.
            value = max(values, key=abs) * 0.001
            method = "legacy duplicate pair: raw µS/cm ÷ 1000"
        elif MICRO_S_PER_CM in units and CANONICAL_UNIT_URI in units:
            # Zero-valued legacy observations collapse to one DISTINCT value.
            value = max(values, key=abs) * 0.001
            method = "legacy mixed units: µS/cm ÷ 1000"
        elif len(units) == 1 and units[0] == MICRO_S_PER_CM:
            value = values[0] * 0.001
            method = "µS/cm ÷ 1000"
        elif (
            legacy_graph
            and sensor.startswith("http://example.com/waterinfo/")
            and units == [CANONICAL_UNIT_URI]
        ):
            # The former converter wrote SI S/m but assigned the mS/cm IRI.
            nonzero = sorted((abs(item), item) for item in values if abs(item) > 1e-12)
            has_corrected_pair = (
                len(nonzero) >= 2
                and 9.9 <= nonzero[-1][0] / nonzero[0][0] <= 10.1
            )
            if has_corrected_pair:
                value = max(values, key=abs)
                method = "legacy + corrected duplicate: kept mS/cm value"
            else:
                value = values[0] * 10.0
                method = "legacy S/m mislabel: × 10"
        elif units == [CANONICAL_UNIT_URI]:
            value = values[0]
            method = "already mS/cm"
        else:
            value = values[0]
            method = "unit unavailable; value unchanged"

        normalized.append(
            {
                "observation": row["observation"],
                "sensor": sensor,
                "time": row["time"],
                "result": value,
                "raw_values": values,
                "source_units": units,
                "normalization": method,
            }
        )
        sensor_report = report.setdefault(
            sensor,
            {
                "sensor": sensor,
                "label": sensor_label(sensor),
                "source_units": set(),
                "methods": set(),
                "canonical_unit": CANONICAL_UNIT_URI,
                "legacy_graph_repair": legacy_graph,
            },
        )
        sensor_report["source_units"].update(units or ["unavailable"])
        sensor_report["methods"].add(method)

    serializable_report = []
    for item in report.values():
        item["source_units"] = sorted(item["source_units"])
        item["methods"] = sorted(item["methods"])
        serializable_report.append(item)
    return normalized, serializable_report
