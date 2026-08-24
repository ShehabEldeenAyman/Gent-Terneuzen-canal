"""Shared, leakage-safe utilities for the paper comparison notebooks.

The notebooks compare two representations under one experimental contract:

* ``unrestricted_72h``: five unshifted sensor histories over 72 hours.
* ``manual_42h``: the paper's fixed Terneuzen-to-target lag hypothesis,
  represented by the target level, one- and two-hour target changes, and the
  Terneuzen value shifted by exactly 42 hours.

All scalers are fit on January-July 2025, August is reserved for model
selection/calibration, and September is held out for final evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import sys
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler


RESAMPLE_MINUTES = 15
STEPS_PER_HOUR = 60 // RESAMPLE_MINUTES
FORECAST_HOURS = 4
FORECAST_STEPS = FORECAST_HOURS * STEPS_PER_HOUR
UNRESTRICTED_HOURS = 72
UNRESTRICTED_STEPS = UNRESTRICTED_HOURS * STEPS_PER_HOUR
MANUAL_LAG_HOURS = 42
MANUAL_LAG_STEPS = MANUAL_LAG_HOURS * STEPS_PER_HOUR
MANUAL_SEQUENCE_HOURS = 42
MANUAL_SEQUENCE_STEPS = MANUAL_SEQUENCE_HOURS * STEPS_PER_HOUR
TRAIN_STRIDE_STEPS = STEPS_PER_HOUR

TRAIN_PERIOD = ("2025-01-01", "2025-07-31 23:59:59")
VALIDATION_PERIOD = ("2025-08-01", "2025-08-31 23:59:59")
TEST_PERIOD = ("2025-09-01", "2025-09-30 23:59:59")
SPLIT_PERIODS = {
    "train": TRAIN_PERIOD,
    "validation": VALIDATION_PERIOD,
    "test": TEST_PERIOD,
}

SENSORS = {
    "Terneuzen": "http://example.com/waterinfo/289441042",
    "Westdorpe": "http://example.com/waterinfo/289435042",
    "Gent - far": "http://example.com/waterinfo/289429042",
    "Gent - near": "http://example.com/waterinfo/289423042",
    "Indusii": "http://example.com/waterlink/111111111",
}
SENSOR_NAMES = list(SENSORS)
TARGET = "Indusii"


@dataclass
class SplitData:
    X: np.ndarray
    y_delta: np.ndarray
    baseline: np.ndarray
    forecast_times: pd.DatetimeIndex


@dataclass
class RepresentationData:
    name: str
    feature_names: list[str]
    splits: dict[str, SplitData]
    input_scaler: StandardScaler | None
    target_scale: np.ndarray


def repository_root() -> Path:
    """Find the repository when called from its root or notebook directory."""
    candidates = [Path.cwd().resolve(), Path.cwd().resolve().parent]
    root = next((path for path in candidates if (path / "lag_analytics_workspace").is_dir()), None)
    if root is None:
        raise RuntimeError(
            "Could not locate the repository root. Start Jupyter from the repository "
            "root or from time_series_analysis."
        )
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return root


def load_prepared_observations() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Read the five QUDT-normalized series from Fuseki and prepare a causal grid."""
    repository_root()
    from lag_analytics_workspace.fuseki import DEFAULT_GRAPH_URI, FusekiClient

    graph_uri = os.getenv("ANALYTICS_DEFAULT_GRAPH_URI", DEFAULT_GRAPH_URI)
    client = FusekiClient(timeout=180)
    raw = client.observations(
        graph_uri,
        SENSORS.values(),
        limit=250_000,
        cache_seconds=0,
    )
    raw["time"] = pd.to_datetime(raw["time"], utc=True)
    raw["result"] = pd.to_numeric(raw["result"], errors="coerce")
    wide = (
        raw.pivot_table(index="time", columns="sensor", values="result", aggfunc="mean")
        .rename(columns={uri: name for name, uri in SENSORS.items()})
        .sort_index()
    )
    missing = [name for name in SENSOR_NAMES if name not in wide.columns]
    if missing:
        raise RuntimeError(f"Fuseki did not return required sensors: {missing}")

    data = wide[SENSOR_NAMES].apply(pd.to_numeric, errors="coerce")
    first = data.apply(pd.Series.first_valid_index)
    last = data.apply(pd.Series.last_valid_index)
    common_start, common_end = first.max(), last.min()
    if pd.isna(common_start) or pd.isna(common_end) or common_start >= common_end:
        raise RuntimeError("The five sensors do not have a valid common interval.")

    data = data.loc[common_start:common_end].resample(f"{RESAMPLE_MINUTES}min").mean()
    data = data.interpolate(method="time", limit=4, limit_area="inside")
    # Causal two-hour smoothing: the current and seven preceding samples only.
    data = data.rolling(2 * STEPS_PER_HOUR, min_periods=2 * STEPS_PER_HOUR).mean()

    coverage = pd.DataFrame(
        {
            "first observation": first,
            "last observation": last,
            "missing after preparation": data.isna().sum(),
            "minimum mS/cm": data.min(),
            "maximum mS/cm": data.max(),
        }
    )
    unit_report = pd.DataFrame(raw.attrs.get("unit_report", []))
    if not unit_report.empty:
        unit_report["sensor_name"] = unit_report["sensor"].map(
            {uri: name for name, uri in SENSORS.items()}
        )
    return data, coverage, unit_report


def manual_feature_frame(data: pd.DataFrame) -> pd.DataFrame:
    """Create the four features stated in the paper's 42-hour ablation."""
    target = data[TARGET]
    return pd.DataFrame(
        {
            "current_target": target,
            "target_change_1h": target - target.shift(STEPS_PER_HOUR),
            "target_change_2h": target - target.shift(2 * STEPS_PER_HOUR),
            "terneuzen_lag_42h": data["Terneuzen"].shift(MANUAL_LAG_STEPS),
        },
        index=data.index,
    )


def _period_bounds(period: tuple[str, str]) -> tuple[pd.Timestamp, pd.Timestamp]:
    return pd.Timestamp(period[0], tz="UTC"), pd.Timestamp(period[1], tz="UTC")


def _shared_origins(
    data: pd.DataFrame,
    unrestricted_values: np.ndarray,
    manual_values: np.ndarray,
    manual_window_steps: int,
    period: tuple[str, str],
    stride_steps: int,
) -> np.ndarray:
    """Return origins valid under both representations and the full future target."""
    target = data[TARGET].to_numpy(dtype=np.float32)
    index = pd.DatetimeIndex(data.index)
    start_time, end_time = _period_bounds(period)
    earliest = max(UNRESTRICTED_STEPS, manual_window_steps)
    origins: list[int] = []
    for s in range(earliest, len(data) - FORECAST_STEPS + 1, stride_steps):
        if index[s] < start_time or index[s + FORECAST_STEPS - 1] > end_time:
            continue
        if not np.isfinite(unrestricted_values[s - UNRESTRICTED_STEPS : s]).all():
            continue
        if not np.isfinite(manual_values[s - manual_window_steps : s]).all():
            continue
        if not np.isfinite(target[s - 1 : s + FORECAST_STEPS]).all():
            continue
        origins.append(s)
    return np.asarray(origins, dtype=np.int64)


def _targets_for_origins(
    data: pd.DataFrame, origins: np.ndarray
) -> tuple[np.ndarray, np.ndarray, pd.DatetimeIndex]:
    target = data[TARGET].to_numpy(dtype=np.float32)
    baselines = target[origins - 1]
    future = np.stack([target[s : s + FORECAST_STEPS] for s in origins]).astype(np.float32)
    y_delta = future - baselines[:, None]
    times = pd.DatetimeIndex(data.index[origins + FORECAST_STEPS - 1])
    return y_delta, baselines, times


def build_classical_datasets(data: pd.DataFrame) -> dict[str, RepresentationData]:
    """Build matched full-history and compact manual-lag arrays for classical ML."""
    unrestricted = data[SENSOR_NAMES]
    manual = manual_feature_frame(data)
    unrestricted_values = unrestricted.to_numpy(dtype=np.float32)
    manual_values = manual.to_numpy(dtype=np.float32)

    origins = {
        name: _shared_origins(
            data,
            unrestricted_values,
            manual_values,
            manual_window_steps=1,
            period=period,
            stride_steps=TRAIN_STRIDE_STEPS if name == "train" else 1,
        )
        for name, period in SPLIT_PERIODS.items()
    }
    if any(len(values) == 0 for values in origins.values()):
        raise RuntimeError(f"Empty split(s): {[k for k, v in origins.items() if len(v) == 0]}")

    result: dict[str, RepresentationData] = {}
    for representation in ("unrestricted_72h", "manual_42h"):
        splits: dict[str, SplitData] = {}
        for split_name, split_origins in origins.items():
            y_delta, baseline, times = _targets_for_origins(data, split_origins)
            if representation == "unrestricted_72h":
                X = np.stack(
                    [
                        unrestricted_values[s - UNRESTRICTED_STEPS : s].reshape(-1)
                        for s in split_origins
                    ]
                ).astype(np.float32)
                names = [
                    f"{sensor}_t-{UNRESTRICTED_STEPS - step}"
                    for step in range(UNRESTRICTED_STEPS)
                    for sensor in SENSOR_NAMES
                ]
            else:
                X = manual_values[split_origins - 1].astype(np.float32)
                names = list(manual.columns)
            splits[split_name] = SplitData(X, y_delta, baseline, times)

        target_scale = splits["train"].y_delta.std(axis=0)
        target_scale = np.where(target_scale < 1e-6, 1.0, target_scale).astype(np.float32)
        result[representation] = RepresentationData(
            name=representation,
            feature_names=names,
            splits=splits,
            input_scaler=None,
            target_scale=target_scale,
        )
    return result


def build_neural_datasets(data: pd.DataFrame) -> dict[str, RepresentationData]:
    """Build matched sequence arrays for the LSTM/TCN comparison.

    The manual neural representation extends the paper's four scalar features
    through a 42-hour sequence. Its last row is exactly the compact feature vector
    used by the classical ablation.
    """
    frames = {
        "unrestricted_72h": data[SENSOR_NAMES].copy(),
        "manual_42h": manual_feature_frame(data),
    }
    window_steps = {
        "unrestricted_72h": UNRESTRICTED_STEPS,
        "manual_42h": MANUAL_SEQUENCE_STEPS,
    }
    scalers: dict[str, StandardScaler] = {}
    scaled: dict[str, np.ndarray] = {}
    for name, frame in frames.items():
        train_rows = frame.loc[TRAIN_PERIOD[0] : TRAIN_PERIOD[1]].dropna()
        if train_rows.empty:
            raise RuntimeError(f"No complete training rows for {name}.")
        scaler = StandardScaler().fit(train_rows)
        scalers[name] = scaler
        scaled[name] = scaler.transform(frame).astype(np.float32)

    origins: dict[str, np.ndarray] = {}
    for split_name, period in SPLIT_PERIODS.items():
        stride = TRAIN_STRIDE_STEPS if split_name == "train" else 1
        # Use a temporary combined manual array only for the shared validity test.
        origins[split_name] = _shared_origins(
            data,
            scaled["unrestricted_72h"],
            scaled["manual_42h"],
            manual_window_steps=MANUAL_SEQUENCE_STEPS,
            period=period,
            stride_steps=stride,
        )
    if any(len(values) == 0 for values in origins.values()):
        raise RuntimeError(f"Empty split(s): {[k for k, v in origins.items() if len(v) == 0]}")

    result: dict[str, RepresentationData] = {}
    for representation, frame in frames.items():
        steps = window_steps[representation]
        splits: dict[str, SplitData] = {}
        for split_name, split_origins in origins.items():
            X = np.stack(
                [scaled[representation][s - steps : s] for s in split_origins]
            ).astype(np.float32)
            y_delta, baseline, times = _targets_for_origins(data, split_origins)
            splits[split_name] = SplitData(X, y_delta, baseline, times)
        target_scale = splits["train"].y_delta.std(axis=0)
        target_scale = np.where(target_scale < 1e-6, 1.0, target_scale).astype(np.float32)
        result[representation] = RepresentationData(
            name=representation,
            feature_names=list(frame.columns),
            splits=splits,
            input_scaler=scalers[representation],
            target_scale=target_scale,
        )
    return result


def validation_calibration(predicted_delta: np.ndarray, actual_delta: np.ndarray) -> np.ndarray:
    """Fit one conservative correction weight per horizon on validation only."""
    numerator = np.sum(predicted_delta * actual_delta, axis=0)
    denominator = np.sum(predicted_delta**2, axis=0)
    weights = np.divide(
        numerator,
        denominator,
        out=np.zeros_like(numerator, dtype=np.float64),
        where=denominator > 1e-12,
    )
    return np.clip(weights, 0.0, 1.0).astype(np.float32)


def score_absolute(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    return {
        "MAE": float(mean_absolute_error(actual, predicted)),
        "RMSE": float(np.sqrt(mean_squared_error(actual, predicted))),
        "R2": float(r2_score(actual, predicted)),
    }


def evaluation_rows(
    model_name: str,
    representation: str,
    split: SplitData,
    predicted_delta: np.ndarray,
) -> tuple[list[dict], pd.DataFrame]:
    """Return overall/endpoint/event metrics and per-horizon diagnostics."""
    actual = split.baseline[:, None] + split.y_delta
    predicted = split.baseline[:, None] + predicted_delta
    persistence = np.repeat(split.baseline[:, None], FORECAST_STEPS, axis=1)
    persistence_scores = score_absolute(actual.ravel(), persistence.ravel())
    model_scores = score_absolute(actual.ravel(), predicted.ravel())

    event_size = np.max(np.abs(split.y_delta), axis=1)
    event_mask = event_size >= np.quantile(event_size, 0.90)
    event_model = score_absolute(actual[event_mask].ravel(), predicted[event_mask].ravel())
    event_persistence = score_absolute(actual[event_mask].ravel(), persistence[event_mask].ravel())

    endpoint_model = score_absolute(actual[:, -1], predicted[:, -1])
    endpoint_persistence = score_absolute(actual[:, -1], persistence[:, -1])
    rows = [
        {
            "Model": model_name,
            "Representation": representation,
            "Scope": "all horizons",
            **model_scores,
            "Persistence RMSE": persistence_scores["RMSE"],
            "RMSE skill": 1.0 - model_scores["RMSE"] / persistence_scores["RMSE"],
            "Samples": len(split.X),
        },
        {
            "Model": model_name,
            "Representation": representation,
            "Scope": "4-hour endpoint",
            **endpoint_model,
            "Persistence RMSE": endpoint_persistence["RMSE"],
            "RMSE skill": 1.0 - endpoint_model["RMSE"] / endpoint_persistence["RMSE"],
            "Samples": len(split.X),
        },
        {
            "Model": model_name,
            "Representation": representation,
            "Scope": "largest 10% changes",
            **event_model,
            "Persistence RMSE": event_persistence["RMSE"],
            "RMSE skill": 1.0 - event_model["RMSE"] / event_persistence["RMSE"],
            "Samples": int(event_mask.sum()),
        },
    ]

    horizon_rows = []
    for step in range(FORECAST_STEPS):
        model_step = score_absolute(actual[:, step], predicted[:, step])
        persistence_step = score_absolute(actual[:, step], persistence[:, step])
        horizon_rows.append(
            {
                "Model": model_name,
                "Representation": representation,
                "Lead minutes": (step + 1) * RESAMPLE_MINUTES,
                **model_step,
                "Persistence RMSE": persistence_step["RMSE"],
                "RMSE skill": 1.0 - model_step["RMSE"] / persistence_step["RMSE"],
            }
        )
    predictions = pd.DataFrame(
        {
            "Actual": actual[:, -1],
            "Prediction": predicted[:, -1],
            "Persistence": persistence[:, -1],
        },
        index=split.forecast_times,
    )
    return rows, pd.DataFrame(horizon_rows), predictions


def split_shape_table(datasets: dict[str, RepresentationData]) -> pd.DataFrame:
    rows = []
    for representation, dataset in datasets.items():
        for split_name, split in dataset.splits.items():
            rows.append(
                {
                    "Representation": representation,
                    "Split": split_name,
                    "X shape": str(split.X.shape),
                    "y shape": str(split.y_delta.shape),
                    "First forecast": split.forecast_times.min(),
                    "Last forecast": split.forecast_times.max(),
                }
            )
    return pd.DataFrame(rows)
