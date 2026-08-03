"""Standalone API for the interactive lag-analysis workspace.

Run from the repository root with:
    uvicorn lag_analytics_workspace.server:app --reload --port 8010
"""

from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import __version__
from .analysis import (
    deep_learning,
    describe_data,
    lag_analysis,
    machine_learning,
    matrix_profile,
    prepare_observations,
)
from .fuseki import DEFAULT_GRAPH_URI, FusekiClient, FusekiError, query_url


app = FastAPI(
    title="CanalOps lag analytics",
    version=__version__,
    description="Independent time-series analytics API reading SOSA observations from Fuseki.",
)
origins = [
    value.strip()
    for value in os.getenv(
        "ANALYTICS_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if value.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
client = FusekiClient()


class AnalysisRequest(BaseModel):
    graph_uri: str = DEFAULT_GRAPH_URI
    target_sensor: str
    upstream_sensors: list[str] = Field(min_length=1)
    resample_minutes: int = Field(default=15, ge=5, le=120)
    observation_limit: int = Field(default=50_000, ge=100, le=250_000)
    max_lag_hours: int = Field(default=48, ge=1, le=168)


class MachineLearningRequest(AnalysisRequest):
    model_name: str = "xgboost"
    forecast_horizon_hours: float = Field(default=1, ge=0.25, le=48)


class DeepLearningRequest(AnalysisRequest):
    lookback_hours: int = Field(default=48, ge=2, le=168)
    forecast_horizon_hours: int = Field(default=4, ge=1, le=48)
    epochs: int = Field(default=3, ge=1, le=20)


class MatrixProfileRequest(AnalysisRequest):
    window_hours: int = Field(default=24, ge=1, le=168)


def _frame(request: AnalysisRequest):
    sensors = list(dict.fromkeys([*request.upstream_sensors, request.target_sensor]))
    raw = client.observations(
        request.graph_uri, sensors, limit=request.observation_limit
    )
    return raw, prepare_observations(raw, request.resample_minutes)


def _execute(operation):
    try:
        return operation()
    except (ValueError, FusekiError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.get("/")
def root():
    return {
        "service": "CanalOps lag analytics",
        "version": __version__,
        "documentation": "/docs",
    }


@app.get("/api/health")
def health():
    return {
        "service": "online",
        "fuseki_connected": client.health(),
        "fuseki_query_endpoint": query_url(),
        "default_graph": DEFAULT_GRAPH_URI,
    }


@app.get("/api/graphs")
def graphs():
    return _execute(lambda: {"graphs": client.graphs(), "default": DEFAULT_GRAPH_URI})


@app.get("/api/sensors")
def sensors(graph_uri: str = Query(default=DEFAULT_GRAPH_URI)):
    return _execute(lambda: {"graph_uri": graph_uri, "sensors": client.sensors(graph_uri)})


@app.post("/api/data")
def data_preview(request: AnalysisRequest):
    def run():
        raw, frame = _frame(request)
        return describe_data(frame, len(raw))

    return _execute(run)


@app.post("/api/lag")
def lag(request: AnalysisRequest):
    return _execute(
        lambda: lag_analysis(
            _frame(request)[1],
            request.target_sensor,
            request.upstream_sensors,
            request.resample_minutes,
            request.max_lag_hours,
        )
    )


@app.post("/api/machine-learning")
def ml(request: MachineLearningRequest):
    return _execute(
        lambda: machine_learning(
            _frame(request)[1],
            request.target_sensor,
            request.upstream_sensors,
            request.model_name,
            request.resample_minutes,
            request.max_lag_hours,
            request.forecast_horizon_hours,
        )
    )


@app.post("/api/deep-learning")
def dl(request: DeepLearningRequest):
    return _execute(
        lambda: deep_learning(
            _frame(request)[1],
            request.target_sensor,
            request.upstream_sensors,
            request.resample_minutes,
            request.lookback_hours,
            request.forecast_horizon_hours,
            request.epochs,
        )
    )


@app.post("/api/matrix-profile")
def profile(request: MatrixProfileRequest):
    return _execute(
        lambda: matrix_profile(
            _frame(request)[1],
            [*request.upstream_sensors, request.target_sensor],
            request.resample_minutes,
            request.window_hours,
        )
    )
