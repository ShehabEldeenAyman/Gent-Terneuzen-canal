"""Leakage-safe TCN utilities for forecasting conductivity at Indusii.

The functions in this module deliberately start from the wide, unsmoothed frame
created by ``lag_analysis_fuseki.ipynb``.  They limit interpolation to short
internal gaps, use causal smoothing, estimate propagation lags on training data
only, reject windows that cross missing-data gaps, and predict only the Indusii
target rather than reconstructing all five stations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler


SENSOR_URIS = {
    "Terneuzen": "http://example.com/waterinfo/289429042",
    "Westdorpe": "http://example.com/waterinfo/289435042",
    "Gent - far": "http://example.com/waterinfo/289441042",
    "Gent - near": "http://example.com/waterinfo/289423042",
    "Indusii": "http://example.com/waterlink/111111111",
}

TARGET_COLUMN = "Indusii"
UPSTREAM_COLUMNS = ["Terneuzen", "Westdorpe", "Gent - far", "Gent - near"]
CANAL_ORDER = ["Terneuzen", "Westdorpe", "Gent - far", "Gent - near", "Indusii"]
PHYSICAL_WINDOWS_HOURS = {
    "Terneuzen": (35.0, 48.0),
    "Westdorpe": (20.0, 38.0),
    "Gent - far": (10.0, 24.0),
    "Gent - near": (0.0, 4.0),
}


@dataclass
class PreparedTCNData:
    frame: pd.DataFrame
    common_start: pd.Timestamp
    common_end: pd.Timestamp
    missing_after_short_fill: dict[str, int]


@dataclass
class TCNExperiment:
    horizon_hours: float
    horizon_steps: int
    model: object
    history: object
    metrics: pd.DataFrame
    prediction_frame: pd.DataFrame
    split_counts: dict[str, int]
    feature_names: list[str]
    target_scale: np.ndarray
    calibration_weights: np.ndarray


def prepare_tcn_frame(
    wide_frame: pd.DataFrame,
    resample_minutes: int = 15,
    max_interpolation_steps: int = 4,
    smoothing_steps: int = 8,
) -> PreparedTCNData:
    """Create a five-station frame without extrapolating sensor tails.

    Only internal gaps of at most ``max_interpolation_steps`` are interpolated.
    Longer gaps remain NaN and are rejected later by the window builder.
    Smoothing is trailing/causal, so a value at time t never uses t+1.
    """

    missing_columns = [uri for uri in SENSOR_URIS.values() if uri not in wide_frame.columns]
    if missing_columns:
        raise KeyError("Missing required sensor columns: " + ", ".join(missing_columns))

    selected = wide_frame[list(SENSOR_URIS.values())].rename(
        columns={uri: label for label, uri in SENSOR_URIS.items()}
    )
    selected.index = pd.to_datetime(selected.index, utc=True)
    selected = selected.sort_index().apply(pd.to_numeric, errors="coerce")

    first_times = selected.apply(pd.Series.first_valid_index)
    last_times = selected.apply(pd.Series.last_valid_index)
    if first_times.isna().any() or last_times.isna().any():
        empty = first_times[first_times.isna()].index.tolist()
        raise ValueError("Sensors without observations: " + ", ".join(empty))

    common_start = max(first_times)
    common_end = min(last_times)
    if common_start >= common_end:
        raise ValueError("The selected sensors do not have a shared observation period.")

    frequency = f"{int(resample_minutes)}min"
    frame = selected.loc[common_start:common_end].resample(frequency).mean()
    frame = frame.interpolate(
        method="time",
        limit=max(0, int(max_interpolation_steps)),
        limit_area="inside",
    )
    frame = frame.rolling(
        window=max(1, int(smoothing_steps)),
        min_periods=max(1, int(smoothing_steps)),
    ).mean()

    return PreparedTCNData(
        frame=frame,
        common_start=common_start,
        common_end=common_end,
        missing_after_short_fill={name: int(value) for name, value in frame.isna().sum().items()},
    )


def estimate_training_lags(
    frame: pd.DataFrame,
    training_end: str | pd.Timestamp = "2025-07-31 23:45:00+00:00",
    resample_minutes: int = 15,
    smoothing_hours: float = 2.0,
    baseline_hours: float = 24.0,
) -> dict[str, dict[str, float | int]]:
    """Estimate physically constrained upstream lags using training data only."""

    training = frame.loc[:pd.Timestamp(training_end)].copy()
    short_steps = max(1, round(smoothing_hours * 60 / resample_minutes))
    baseline_steps = max(short_steps + 1, round(baseline_hours * 60 / resample_minutes))
    smoothed = training.rolling(short_steps, min_periods=short_steps).mean()
    baseline = training.rolling(baseline_steps, min_periods=baseline_steps).mean()
    signal = smoothed - baseline
    results: dict[str, dict[str, float | int]] = {}

    for station in UPSTREAM_COLUMNS:
        low_hours, high_hours = PHYSICAL_WINDOWS_HOURS[station]
        low_step = round(low_hours * 60 / resample_minutes)
        high_step = round(high_hours * 60 / resample_minutes)
        correlations = np.asarray(
            [signal[station].shift(step).corr(signal[TARGET_COLUMN]) for step in range(low_step, high_step + 1)],
            dtype=float,
        )
        if correlations.size == 0 or np.isnan(correlations).all():
            raise ValueError(f"No finite training-period lag correlation was found for {station}.")
        offset = int(np.nanargmax(correlations))
        step = low_step + offset
        results[station] = {
            "steps": step,
            "hours": step * resample_minutes / 60,
            "correlation": float(correlations[offset]),
        }
    return results


def build_tcn_features(
    frame: pd.DataFrame,
    lag_results: dict[str, dict[str, float | int]],
    resample_minutes: int = 15,
) -> tuple[pd.DataFrame, list[str]]:
    """Add physically meaningful channels while retaining raw station histories."""

    features = frame[CANAL_ORDER].copy()
    feature_names = list(CANAL_ORDER)

    for upstream, downstream in zip(CANAL_ORDER[:-1], CANAL_ORDER[1:]):
        name = f"gradient__{upstream}__to__{downstream}"
        features[name] = frame[upstream] - frame[downstream]
        feature_names.append(name)

    steps_per_hour = max(1, round(60 / resample_minutes))
    for hours in (1, 2):
        name = f"indusii_delta_{hours}h"
        features[name] = frame[TARGET_COLUMN].diff(hours * steps_per_hour)
        feature_names.append(name)

    for station in UPSTREAM_COLUMNS:
        lag_steps = int(lag_results[station]["steps"])
        name = f"lag_aligned__{station}"
        features[name] = frame[station].shift(lag_steps)
        feature_names.append(name)

    minute_of_day = features.index.hour * 60 + features.index.minute
    day_of_year = features.index.dayofyear
    features["time_sin"] = np.sin(2 * np.pi * minute_of_day / 1_440)
    features["time_cos"] = np.cos(2 * np.pi * minute_of_day / 1_440)
    features["year_sin"] = np.sin(2 * np.pi * day_of_year / 365.25)
    features["year_cos"] = np.cos(2 * np.pi * day_of_year / 365.25)
    feature_names.extend(["time_sin", "time_cos", "year_sin", "year_cos"])
    return features, feature_names


def _window_starts(
    values: np.ndarray,
    target: np.ndarray,
    index: pd.DatetimeIndex,
    lookback_steps: int,
    horizon_steps: int,
    period_start: str,
    period_end: str,
) -> np.ndarray:
    row_valid = np.isfinite(values).all(axis=1) & np.isfinite(target)
    invalid = (~row_valid).astype(np.int32)
    cumulative = np.concatenate(([0], np.cumsum(invalid)))
    starts = np.arange(lookback_steps, len(index) - horizon_steps + 1)
    whole_window_valid = cumulative[starts + horizon_steps] == cumulative[starts - lookback_steps]

    start_time = pd.Timestamp(period_start, tz="UTC")
    end_time = pd.Timestamp(period_end, tz="UTC")
    forecast_starts = index[starts]
    forecast_ends = index[starts + horizon_steps - 1]
    inside_period = (forecast_starts >= start_time) & (forecast_ends <= end_time)
    return starts[whole_window_valid & inside_period]


def _make_sequence(
    values: np.ndarray,
    target: np.ndarray,
    starts: np.ndarray,
    lookback_steps: int,
    horizon_steps: int,
    batch_size: int,
    shuffle: bool,
    target_scale: np.ndarray,
):
    import tensorflow as tf

    class WindowSequence(tf.keras.utils.Sequence):
        def __init__(self):
            super().__init__()
            self.order = np.arange(len(starts))

        def __len__(self):
            return int(np.ceil(len(starts) / batch_size))

        def __getitem__(self, batch_index):
            positions = self.order[batch_index * batch_size : (batch_index + 1) * batch_size]
            selected = starts[positions]
            x = np.stack([values[s - lookback_steps : s] for s in selected]).astype(np.float32)
            base = target[selected - 1]
            future = np.stack([target[s : s + horizon_steps] for s in selected])
            y_delta = ((future - base[:, None]) / target_scale[None, :]).astype(np.float32)
            return x, y_delta

        def on_epoch_end(self):
            if shuffle:
                np.random.default_rng().shuffle(self.order)

    return WindowSequence()


def build_tcn(
    lookback_steps: int,
    n_features: int,
    horizon_steps: int,
    filters: int = 24,
    kernel_size: int = 5,
    dropout: float = 0.15,
):
    """Build a compact residual TCN with a receptive field over 72 hours."""

    import tensorflow as tf
    from tensorflow.keras import Model, layers

    inputs = layers.Input(shape=(lookback_steps, n_features), name="history")
    x = inputs
    regularizer = tf.keras.regularizers.l2(1e-5)
    for dilation in (1, 2, 4, 8, 16, 32):
        residual = x
        if x.shape[-1] != filters:
            residual = layers.Conv1D(filters, 1, padding="same")(x)
        for _ in range(2):
            x = layers.Conv1D(
                filters,
                kernel_size,
                padding="causal",
                dilation_rate=dilation,
                kernel_regularizer=regularizer,
            )(x)
            x = layers.LayerNormalization()(x)
            x = layers.Activation("swish")(x)
            x = layers.SpatialDropout1D(dropout)(x)
        x = layers.Add()([x, residual])
        x = layers.Activation("swish")(x)

    encoded = layers.Concatenate()([x[:, -1, :], inputs[:, -1, :]])
    encoded = layers.Dense(64, activation="swish", kernel_regularizer=regularizer)(encoded)
    encoded = layers.Dropout(dropout)(encoded)
    # A zero-initialized forecast head makes the untrained network equal to the
    # persistence forecast. Training therefore learns corrections to a strong
    # operational baseline instead of beginning with arbitrary large deltas.
    output = layers.Dense(
        horizon_steps,
        kernel_initializer="zeros",
        bias_initializer="zeros",
        name="scaled_indusii_delta",
    )(encoded)
    return Model(inputs, output, name=f"Indusii_TCN_{horizon_steps}_steps")


def _scores(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    return {
        "mae": float(mean_absolute_error(actual, predicted)),
        "rmse": float(np.sqrt(mean_squared_error(actual, predicted))),
        "r2": float(r2_score(actual, predicted)),
    }


def train_tcn_experiment(
    features: pd.DataFrame,
    feature_names: Iterable[str],
    horizon_hours: float,
    resample_minutes: int = 15,
    lookback_hours: int = 72,
    train_period: tuple[str, str] = ("2025-01-01", "2025-07-31 23:59:59"),
    validation_period: tuple[str, str] = ("2025-08-01", "2025-08-31 23:59:59"),
    test_period: tuple[str, str] = ("2025-09-01", "2025-09-30 23:59:59"),
    epochs: int = 30,
    batch_size: int = 64,
    random_seed: int = 42,
    verbose: int = 1,
) -> TCNExperiment:
    """Train and evaluate one direct Indusii delta-forecast TCN."""

    import tensorflow as tf

    feature_names = list(feature_names)
    lookback_steps = round(lookback_hours * 60 / resample_minutes)
    horizon_steps = round(horizon_hours * 60 / resample_minutes)
    if horizon_steps < 1:
        raise ValueError("horizon_hours must represent at least one sample.")

    train_rows = features.loc[train_period[0] : train_period[1], feature_names].dropna()
    if train_rows.empty:
        raise ValueError("No complete training rows are available for feature scaling.")
    input_scaler = StandardScaler().fit(train_rows)
    scaled_values = input_scaler.transform(features[feature_names]).astype(np.float32)
    target = features[TARGET_COLUMN].to_numpy(dtype=np.float32)
    index = pd.DatetimeIndex(features.index)

    split_periods = {
        "train": train_period,
        "validation": validation_period,
        "test": test_period,
    }
    starts = {
        name: _window_starts(
            scaled_values,
            target,
            index,
            lookback_steps,
            horizon_steps,
            period[0],
            period[1],
        )
        for name, period in split_periods.items()
    }
    if any(len(value) == 0 for value in starts.values()):
        empty = [name for name, value in starts.items() if len(value) == 0]
        raise ValueError("No complete windows for split(s): " + ", ".join(empty))

    # Scale every lead time independently. Without this, the small short-lead
    # changes are overwhelmed by the wider distribution at later lead times.
    train_base = target[starts["train"] - 1]
    train_delta = np.stack(
        [target[s : s + horizon_steps] - target[s - 1] for s in starts["train"]]
    )
    target_scale = np.nanstd(train_delta, axis=0).astype(np.float32)
    target_scale = np.where(target_scale < 1e-4, 1.0, target_scale).astype(np.float32)

    sequences = {
        name: _make_sequence(
            scaled_values,
            target,
            value,
            lookback_steps,
            horizon_steps,
            batch_size,
            shuffle=name == "train",
            target_scale=target_scale,
        )
        for name, value in starts.items()
    }

    tf.keras.utils.set_random_seed(random_seed)
    model = build_tcn(lookback_steps, len(feature_names), horizon_steps)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=3e-4, clipnorm=1.0),
        loss=tf.keras.losses.Huber(delta=1.0),
        metrics=[tf.keras.metrics.MeanAbsoluteError(name="delta_mae")],
    )
    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=6, min_delta=1e-5, restore_best_weights=True
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=3, min_lr=1e-6
        ),
    ]
    history = model.fit(
        sequences["train"],
        validation_data=sequences["validation"],
        epochs=max(1, int(epochs)),
        callbacks=callbacks,
        verbose=verbose,
    )

    # Estimate a conservative blend with persistence on validation data. A
    # weight of zero is persistence; one uses the complete learned correction.
    # Clipping to [0, 1] prevents an unstable model from being amplified.
    validation_prediction = (
        model.predict(sequences["validation"], verbose=0) * target_scale[None, :]
    )
    validation_delta = np.stack(
        [target[s : s + horizon_steps] - target[s - 1] for s in starts["validation"]]
    )
    numerator = np.sum(validation_prediction * validation_delta, axis=0)
    denominator = np.sum(validation_prediction**2, axis=0)
    calibration_weights = np.divide(
        numerator,
        denominator,
        out=np.zeros_like(numerator),
        where=denominator > 1e-12,
    )
    calibration_weights = np.clip(calibration_weights, 0.0, 1.0).astype(np.float32)

    predicted_delta = model.predict(sequences["test"], verbose=0) * target_scale[None, :]
    predicted_delta *= calibration_weights[None, :]
    ordered_test = starts["test"]
    actual_delta = np.stack(
        [target[s : s + horizon_steps] - target[s - 1] for s in ordered_test]
    )
    baselines = target[ordered_test - 1]
    actual_absolute = baselines[:, None] + actual_delta
    predicted_absolute = baselines[:, None] + predicted_delta
    persistence = np.repeat(baselines[:, None], horizon_steps, axis=1)

    rows = []
    report_steps = sorted(set([min(horizon_steps, step) for step in (4, 16, horizon_steps)]))
    for step in report_steps:
        actual = actual_absolute[:, step - 1]
        prediction = predicted_absolute[:, step - 1]
        naive = persistence[:, step - 1]
        model_scores = _scores(actual, prediction)
        baseline_scores = _scores(actual, naive)
        rows.append(
            {
                "horizon_hours": step * resample_minutes / 60,
                **{f"tcn_{key}": value for key, value in model_scores.items()},
                **{f"persistence_{key}": value for key, value in baseline_scores.items()},
                "rmse_skill_vs_persistence": 1 - model_scores["rmse"] / baseline_scores["rmse"],
            }
        )

    final_step = horizon_steps - 1
    prediction_frame = pd.DataFrame(
        {
            "forecast_time": index[ordered_test + final_step],
            "actual": actual_absolute[:, final_step],
            "tcn": predicted_absolute[:, final_step],
            "persistence": persistence[:, final_step],
        }
    ).set_index("forecast_time")

    return TCNExperiment(
        horizon_hours=horizon_hours,
        horizon_steps=horizon_steps,
        model=model,
        history=history,
        metrics=pd.DataFrame(rows),
        prediction_frame=prediction_frame,
        split_counts={name: len(value) for name, value in starts.items()},
        feature_names=feature_names,
        target_scale=target_scale,
        calibration_weights=calibration_weights,
    )


def plot_tcn_experiment(experiment: TCNExperiment, start: str | None = None, end: str | None = None):
    """Plot loss curves and the requested test-period forecast slice."""

    import matplotlib.pyplot as plt

    prediction = experiment.prediction_frame.loc[start:end]
    history = experiment.history.history
    fig, axes = plt.subplots(1, 2, figsize=(16, 5))
    axes[0].plot(history["loss"], label="Training")
    axes[0].plot(history["val_loss"], label="Validation")
    axes[0].set_title(f"TCN Huber loss ({experiment.horizon_hours:g}h horizon)")
    axes[0].set_xlabel("Epoch")
    axes[0].legend()
    axes[0].grid(alpha=0.3)

    axes[1].plot(prediction.index, prediction["actual"], label="Actual", linewidth=1.8)
    axes[1].plot(prediction.index, prediction["tcn"], label="TCN", linestyle="--")
    axes[1].plot(prediction.index, prediction["persistence"], label="Persistence", alpha=0.7)
    axes[1].set_title(f"Indusii conductivity forecast ({experiment.horizon_hours:g}h)")
    axes[1].set_ylabel("Conductivity (mS/cm)")
    axes[1].legend()
    axes[1].grid(alpha=0.3)
    fig.tight_layout()
    return fig
