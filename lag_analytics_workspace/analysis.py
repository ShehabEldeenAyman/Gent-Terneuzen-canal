"""Reusable analytics extracted from the lag_analysis notebook's workflow."""

from __future__ import annotations

import math
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.svm import SVR

from .fuseki import sensor_label


PHYSICAL_WINDOWS = {
    "289441042": (35.0, 48.0),
    "289435042": (20.0, 38.0),
    "289429042": (10.0, 24.0),
    "289423042": (0.0, 4.0),
}


def prepare_observations(raw: pd.DataFrame, resample_minutes: int = 15) -> pd.DataFrame:
    """Convert Fuseki's long SOSA result into an aligned numerical time grid."""
    required = {"sensor", "time", "result"}
    if not required.issubset(raw.columns):
        raise ValueError(f"Observation data must contain {sorted(required)}.")
    unit_report = raw.attrs.get("unit_report", [])
    frame = raw.copy()
    frame["time"] = pd.to_datetime(frame["time"], errors="coerce", utc=True)
    frame["result"] = pd.to_numeric(frame["result"], errors="coerce")
    frame = frame.dropna(subset=["time", "result", "sensor"])
    if frame.empty:
        raise ValueError("The selected observations do not contain numeric time-series values.")
    wide = frame.pivot_table(index="time", columns="sensor", values="result", aggfunc="mean")
    wide = wide.sort_index().resample(f"{int(resample_minutes)}min").mean()
    wide = wide.interpolate(method="time", limit_direction="both").dropna(how="all")
    wide.attrs["unit_report"] = unit_report
    return wide


def _sample_indices(length: int, maximum: int) -> np.ndarray:
    if length <= maximum:
        return np.arange(length)
    return np.unique(np.linspace(0, length - 1, maximum, dtype=int))


def _number(value: float | int | np.number | None, digits: int = 6):
    if value is None or not np.isfinite(value):
        return None
    return round(float(value), digits)


def series_payload(frame: pd.DataFrame, maximum_points: int = 1_200) -> list[dict]:
    indices = _sample_indices(len(frame), maximum_points)
    sampled = frame.iloc[indices]
    output = []
    for sensor in sampled.columns:
        points = [
            [timestamp.isoformat(), _number(value)]
            for timestamp, value in sampled[sensor].items()
            if np.isfinite(value)
        ]
        output.append({"sensor": sensor, "label": sensor_label(sensor), "points": points})
    return output


def describe_data(frame: pd.DataFrame, raw_rows: int) -> dict:
    return {
        "raw_rows": int(raw_rows),
        "prepared_rows": int(len(frame)),
        "sensor_count": int(len(frame.columns)),
        "start_time": frame.index.min().isoformat(),
        "end_time": frame.index.max().isoformat(),
        "missing_values": int(frame.isna().sum().sum()),
        "canonical_unit": "mS/cm",
        "unit_normalization": frame.attrs.get("unit_report", []),
        "series": series_payload(frame),
    }


def lag_analysis(
    frame: pd.DataFrame,
    target_sensor: str,
    upstream_sensors: Iterable[str],
    resample_minutes: int = 15,
    max_lag_hours: int = 48,
) -> dict:
    if target_sensor not in frame:
        raise ValueError("The target sensor is not present in the prepared dataset.")
    upstream = [sensor for sensor in upstream_sensors if sensor in frame and sensor != target_sensor]
    if not upstream:
        raise ValueError("Select at least one upstream sensor that has observations.")

    short_window = max(1, round(120 / resample_minutes))
    baseline_window = max(short_window + 1, round(1_440 / resample_minutes))
    smoothed = frame.rolling(short_window, min_periods=1, center=True).mean()
    baseline = frame.rolling(baseline_window, min_periods=1, center=True).mean()
    signal = (smoothed - baseline).dropna()
    max_steps = max(1, round(max_lag_hours * 60 / resample_minutes))
    results = []

    for sensor in upstream:
        correlations = np.asarray(
            [signal[sensor].shift(step).corr(signal[target_sensor]) for step in range(max_steps + 1)],
            dtype=float,
        )
        identifier = sensor.rstrip("/").rsplit("/", 1)[-1]
        min_hours, upper_hours = PHYSICAL_WINDOWS.get(identifier, (0.0, float(max_lag_hours)))
        upper_hours = min(upper_hours, float(max_lag_hours))
        min_hours = min(min_hours, upper_hours)
        start = max(0, round(min_hours * 60 / resample_minutes))
        stop = min(max_steps, round(upper_hours * 60 / resample_minutes))
        window = correlations[start : stop + 1]
        if window.size == 0 or np.isnan(window).all():
            best_step, best_correlation = start, math.nan
        else:
            best_step = start + int(np.nanargmax(window))
            best_correlation = correlations[best_step]
        results.append(
            {
                "sensor": sensor,
                "label": sensor_label(sensor),
                "best_lag_steps": int(best_step),
                "best_lag_hours": _number(best_step * resample_minutes / 60, 2),
                "correlation": _number(best_correlation, 4),
                "search_window_hours": [min_hours, upper_hours],
                "profile": [
                    [round(step * resample_minutes / 60, 2), _number(value, 5)]
                    for step, value in enumerate(correlations)
                ],
            }
        )
    return {
        "target_sensor": target_sensor,
        "target_label": sensor_label(target_sensor),
        "filter": {
            "short_smoothing_hours": round(short_window * resample_minutes / 60, 2),
            "baseline_hours": round(baseline_window * resample_minutes / 60, 2),
        },
        "results": results,
    }


def _feature_matrix(
    frame: pd.DataFrame,
    target_sensor: str,
    upstream_sensors: list[str],
    lag_result: dict,
    resample_minutes: int,
    forecast_horizon_hours: float,
) -> tuple[pd.DataFrame, list[str]]:
    horizon_steps = max(1, round(forecast_horizon_hours * 60 / resample_minutes))
    one_hour = max(1, round(60 / resample_minutes))
    features = pd.DataFrame(index=frame.index)
    features["current_target"] = frame[target_sensor]
    features["target_delta"] = frame[target_sensor].shift(-horizon_steps) - frame[target_sensor]
    features["delta_memory_1h"] = frame[target_sensor] - frame[target_sensor].shift(one_hour)
    features["delta_memory_2h"] = frame[target_sensor] - frame[target_sensor].shift(2 * one_hour)
    lag_by_sensor = {item["sensor"]: item["best_lag_steps"] for item in lag_result["results"]}
    feature_names = ["delta_memory_1h", "delta_memory_2h"]
    for sensor in upstream_sensors:
        if sensor not in frame:
            continue
        name = f"{sensor_label(sensor).lower().replace(' ', '_').replace('·', '')}_lagged"
        features[name] = frame[sensor].shift(int(lag_by_sensor.get(sensor, 0)))
        feature_names.append(name)
    return features.dropna(), feature_names


def machine_learning(
    frame: pd.DataFrame,
    target_sensor: str,
    upstream_sensors: list[str],
    model_name: str = "xgboost",
    resample_minutes: int = 15,
    max_lag_hours: int = 48,
    forecast_horizon_hours: float = 1,
) -> dict:
    lag_result = lag_analysis(
        frame, target_sensor, upstream_sensors, resample_minutes, max_lag_hours
    )
    dataset, feature_names = _feature_matrix(
        frame,
        target_sensor,
        upstream_sensors,
        lag_result,
        resample_minutes,
        forecast_horizon_hours,
    )
    if len(dataset) < 40:
        raise ValueError("At least 40 aligned observations are required for model training.")
    split = min(len(dataset) - 10, max(30, int(len(dataset) * 0.8)))
    train, test = dataset.iloc[:split], dataset.iloc[split:]
    x_train, x_test = train[feature_names], test[feature_names]
    y_train, y_test = train["target_delta"], test["target_delta"]

    normalized_name = model_name.lower()
    if normalized_name == "xgboost":
        try:
            from xgboost import XGBRegressor

            model = XGBRegressor(
                n_estimators=120,
                learning_rate=0.05,
                max_depth=6,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=2,
            )
            display_name = "XGBoost delta regressor"
        except ImportError:
            from sklearn.ensemble import HistGradientBoostingRegressor

            model = HistGradientBoostingRegressor(max_iter=120, random_state=42)
            display_name = "Histogram gradient boosting (XGBoost fallback)"
    elif normalized_name == "svr":
        model = make_pipeline(StandardScaler(), SVR(kernel="rbf", C=100.0, epsilon=0.01))
        display_name = "Scaled radial-basis SVR"
    elif normalized_name == "mlp":
        model = make_pipeline(
            StandardScaler(),
            MLPRegressor(
                hidden_layer_sizes=(64, 32),
                activation="relu",
                solver="adam",
                learning_rate_init=0.01,
                max_iter=300,
                early_stopping=True,
                random_state=42,
            ),
        )
        display_name = "64 × 32 multilayer perceptron"
    else:
        raise ValueError("model_name must be one of: xgboost, svr, mlp.")

    model.fit(x_train, y_train)
    predicted_delta = np.asarray(model.predict(x_test), dtype=float)
    baseline = test["current_target"].to_numpy(dtype=float)
    actual = baseline + y_test.to_numpy(dtype=float)
    predicted = baseline + predicted_delta
    indices = _sample_indices(len(test), 700)
    points = [
        {
            "time": test.index[index].isoformat(),
            "actual": _number(actual[index]),
            "predicted": _number(predicted[index]),
        }
        for index in indices
    ]

    if hasattr(model, "feature_importances_"):
        importances = np.asarray(model.feature_importances_)
    else:
        scored_x = x_test.iloc[: min(500, len(x_test))]
        scored_y = y_test.iloc[: len(scored_x)]
        importances = permutation_importance(
            model, scored_x, scored_y, n_repeats=2, random_state=42, n_jobs=1
        ).importances_mean
    importance = sorted(
        [
            {"feature": name, "importance": _number(value, 5)}
            for name, value in zip(feature_names, importances)
        ],
        key=lambda item: item["importance"] or 0,
        reverse=True,
    )
    return {
        "model": normalized_name,
        "model_label": display_name,
        "train_samples": int(len(train)),
        "test_samples": int(len(test)),
        "train_period": [train.index.min().isoformat(), train.index.max().isoformat()],
        "test_period": [test.index.min().isoformat(), test.index.max().isoformat()],
        "forecast_horizon_hours": forecast_horizon_hours,
        "metrics": {
            "mae": _number(mean_absolute_error(actual, predicted), 3),
            "rmse": _number(math.sqrt(mean_squared_error(actual, predicted)), 3),
            "r2": _number(r2_score(actual, predicted), 4),
        },
        "feature_importance": importance,
        "predictions": points,
        "lags": lag_result["results"],
    }


def deep_learning(
    frame: pd.DataFrame,
    target_sensor: str,
    upstream_sensors: list[str],
    resample_minutes: int = 15,
    lookback_hours: int = 48,
    forecast_horizon_hours: int = 4,
    epochs: int = 3,
    max_training_sequences: int = 4_000,
) -> dict:
    try:
        import tensorflow as tf
        from tensorflow.keras import Model, layers, regularizers
        from tensorflow.keras.callbacks import EarlyStopping
    except ImportError as error:
        raise RuntimeError(
            "TensorFlow is not installed. Install lag_analytics_workspace/requirements.txt."
        ) from error

    selected = [sensor for sensor in upstream_sensors if sensor in frame]
    if target_sensor not in selected:
        selected.append(target_sensor)
    data = frame[selected].dropna()
    time_steps = max(8, round(lookback_hours * 60 / resample_minutes))
    future_steps = max(1, round(forecast_horizon_hours * 60 / resample_minutes))
    if len(data) < time_steps + future_steps + 30:
        raise ValueError(
            f"Deep learning needs at least {time_steps + future_steps + 30} aligned rows; "
            f"the selection has {len(data)}."
        )

    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(data).astype(np.float32)
    target_index = selected.index(target_sensor)
    x_values, y_values, target_times = [], [], []
    for index in range(len(scaled) - time_steps - future_steps + 1):
        x_values.append(scaled[index : index + time_steps])
        y_values.append(scaled[index + time_steps : index + time_steps + future_steps, target_index])
        target_times.append(data.index[index + time_steps : index + time_steps + future_steps])
    x_values = np.asarray(x_values, dtype=np.float32)
    y_values = np.asarray(y_values, dtype=np.float32)
    if len(x_values) > max_training_sequences:
        x_values = x_values[-max_training_sequences:]
        y_values = y_values[-max_training_sequences:]
        target_times = target_times[-max_training_sequences:]
    split = min(len(x_values) - 5, max(20, int(len(x_values) * 0.8)))
    x_train, x_test = x_values[:split], x_values[split:]
    y_train, y_test = y_values[:split], y_values[split:]
    epochs = max(1, min(int(epochs), 20))
    tf.keras.utils.set_random_seed(42)

    regularizer = regularizers.l2(1e-4)
    encoder_input = layers.Input(shape=(time_steps, len(selected)), name="encoder_input")
    encoded = layers.GaussianNoise(0.05)(encoder_input)
    encoded = layers.LSTM(32, return_sequences=True, kernel_regularizer=regularizer)(encoded)
    bottleneck = layers.LSTM(16, name="bottleneck", kernel_regularizer=regularizer)(encoded)
    decoded = layers.RepeatVector(time_steps)(bottleneck)
    decoded = layers.LSTM(16, return_sequences=True)(decoded)
    decoded = layers.LSTM(32, return_sequences=True)(decoded)
    reconstruction = layers.TimeDistributed(
        layers.Dense(len(selected), activation="sigmoid"), name="reconstruction"
    )(decoded)
    autoencoder = Model(encoder_input, reconstruction, name="lag_lstm_autoencoder")
    autoencoder.compile(optimizer=tf.keras.optimizers.Adam(1e-3), loss="mse")
    callbacks = [EarlyStopping(monitor="val_loss", patience=2, restore_best_weights=True)]
    auto_history = autoencoder.fit(
        x_train,
        x_train,
        epochs=epochs,
        batch_size=32,
        validation_split=0.1,
        callbacks=callbacks,
        verbose=0,
    )

    encoder = Model(autoencoder.input, autoencoder.get_layer("bottleneck").output)
    encoder.trainable = False
    forecast_input = layers.Input(shape=(time_steps, len(selected)))
    forecast_output = layers.Dense(future_steps, name="forecast")(encoder(forecast_input))
    forecaster = Model(forecast_input, forecast_output, name="lag_forecaster")
    forecaster.compile(optimizer=tf.keras.optimizers.Adam(1e-3), loss="mse")
    forecast_history = forecaster.fit(
        x_train,
        y_train,
        epochs=epochs,
        batch_size=32,
        validation_split=0.1,
        callbacks=callbacks,
        verbose=0,
    )
    encoder.trainable = True
    forecaster.compile(optimizer=tf.keras.optimizers.Adam(1e-5), loss="mse")
    forecaster.fit(
        x_train,
        y_train,
        epochs=max(1, epochs // 2),
        batch_size=32,
        validation_split=0.1,
        verbose=0,
    )

    predicted_scaled = forecaster.predict(x_test, verbose=0)
    scale = scaler.scale_[target_index]
    minimum = scaler.min_[target_index]
    actual = (y_test - minimum) / scale
    predicted = (predicted_scaled - minimum) / scale
    latest_times = target_times[-1]
    latest = [
        {
            "time": latest_times[index].isoformat(),
            "actual": _number(actual[-1, index]),
            "predicted": _number(predicted[-1, index]),
        }
        for index in range(future_steps)
    ]
    return {
        "model_label": "LSTM autoencoder + frozen-head forecaster",
        "lookback_hours": lookback_hours,
        "forecast_horizon_hours": forecast_horizon_hours,
        "epochs_per_phase": epochs,
        "train_sequences": int(len(x_train)),
        "test_sequences": int(len(x_test)),
        "metrics": {
            "mae": _number(mean_absolute_error(actual.ravel(), predicted.ravel()), 3),
            "rmse": _number(math.sqrt(mean_squared_error(actual.ravel(), predicted.ravel())), 3),
        },
        "forecast": latest,
        "history": {
            "autoencoder_loss": [_number(value, 7) for value in auto_history.history["loss"]],
            "forecast_loss": [_number(value, 7) for value in forecast_history.history["loss"]],
        },
    }


def _profile(vectors: np.ndarray, exclusion: int) -> tuple[np.ndarray, np.ndarray]:
    distances = cdist(vectors, vectors, metric="euclidean") / math.sqrt(vectors.shape[1])
    for index in range(len(distances)):
        start, stop = max(0, index - exclusion), min(len(distances), index + exclusion + 1)
        distances[index, start:stop] = np.inf
    indices = np.argmin(distances, axis=1)
    profile = distances[np.arange(len(distances)), indices]
    return profile, indices


def matrix_profile(
    frame: pd.DataFrame,
    sensors: list[str],
    resample_minutes: int = 15,
    window_hours: int = 24,
) -> dict:
    selected = [sensor for sensor in sensors if sensor in frame]
    if not selected:
        raise ValueError("Select at least one sensor for the matrix profile.")
    values = frame[selected].interpolate(method="time").bfill().ffill()
    requested_window = max(4, round(window_hours * 60 / resample_minutes))
    if len(values) < requested_window * 2 + 5:
        raise ValueError(
            f"A {window_hours}-hour profile needs at least {requested_window * 2 + 5} rows."
        )

    # Bound the fallback calculation while preserving the full time span.
    subsequences = len(values) - requested_window + 1
    factor = max(1, math.ceil(subsequences / 350))
    if factor > 1:
        values = values.iloc[::factor]
    window = max(4, round(requested_window / factor))
    array = values.to_numpy(dtype=float).T
    one_dimensional = []
    normalized_sequences = []
    nearest = None
    for dimension in array:
        sequences = np.lib.stride_tricks.sliding_window_view(dimension, window)
        means = sequences.mean(axis=1, keepdims=True)
        standard = sequences.std(axis=1, keepdims=True)
        normalized = (sequences - means) / np.where(standard < 1e-12, 1.0, standard)
        profile, dimension_nearest = _profile(normalized, max(1, window // 4))
        one_dimensional.append(profile)
        normalized_sequences.append(normalized)
        nearest = dimension_nearest
    one_profile = np.min(np.vstack(one_dimensional), axis=0)
    joint_vectors = np.concatenate(normalized_sequences, axis=1)
    joint_profile, joint_nearest = _profile(joint_vectors, max(1, window // 4))
    times = values.index[: len(joint_profile)]
    motif_index = int(np.nanargmin(joint_profile))
    match_index = int(joint_nearest[motif_index])
    discord_index = int(np.nanargmax(joint_profile))
    sample = _sample_indices(len(joint_profile), 700)
    return {
        "engine": "bounded multidimensional matrix profile",
        "window_hours": window_hours,
        "window_points": int(window),
        "effective_interval_minutes": int(resample_minutes * factor),
        "dimensions": len(selected),
        "sensors": [{"uri": sensor, "label": sensor_label(sensor)} for sensor in selected],
        "one_dimensional": [
            [times[index].isoformat(), _number(one_profile[index], 5)] for index in sample
        ],
        "multidimensional": [
            [times[index].isoformat(), _number(joint_profile[index], 5)] for index in sample
        ],
        "motif": {
            "start_time": times[motif_index].isoformat(),
            "match_time": times[match_index].isoformat(),
            "distance": _number(joint_profile[motif_index], 5),
        },
        "discord": {
            "start_time": times[discord_index].isoformat(),
            "distance": _number(joint_profile[discord_index], 5),
        },
    }
