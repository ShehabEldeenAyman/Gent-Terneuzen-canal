import numpy as np
import pandas as pd

from automating_aligments.automated_alignments import convert_qudt_value
from lag_analytics_workspace.analysis import (
    lag_analysis,
    machine_learning,
    matrix_profile,
    prepare_observations,
)
from lag_analytics_workspace.fuseki import (
    CANONICAL_UNIT_URI,
    MICRO_S_PER_CM,
    normalize_fuseki_observations,
)


TARGET = "http://example.com/waterinfo/111111111"
UPSTREAM = "http://example.com/waterinfo/custom-upstream"


def synthetic_raw(rows=600):
    time = pd.date_range("2025-01-01", periods=rows, freq="15min", tz="UTC")
    upstream = np.sin(np.arange(rows) / 12) + np.sin(np.arange(rows) / 55) * 0.2
    target = np.roll(upstream, 8) + np.random.default_rng(42).normal(0, 0.02, rows)
    return pd.DataFrame(
        {
            "sensor": [UPSTREAM] * rows + [TARGET] * rows,
            "time": list(time.astype(str)) * 2,
            "result": list(upstream) + list(target),
        }
    )


def test_prepare_and_lag_analysis_find_shift():
    frame = prepare_observations(synthetic_raw())
    result = lag_analysis(frame, TARGET, [UPSTREAM], max_lag_hours=6)
    assert result["results"][0]["best_lag_hours"] == 2.0
    assert result["results"][0]["correlation"] > 0.95


def test_machine_learning_returns_predictions():
    frame = prepare_observations(synthetic_raw())
    result = machine_learning(
        frame, TARGET, [UPSTREAM], model_name="svr", max_lag_hours=6
    )
    assert result["test_samples"] > 0
    assert result["predictions"]
    assert set(result["metrics"]) == {"mae", "rmse", "r2"}


def test_matrix_profile_returns_motif_and_discord():
    frame = prepare_observations(synthetic_raw(300))
    result = matrix_profile(frame, [UPSTREAM, TARGET], window_hours=4)
    assert result["dimensions"] == 2
    assert result["multidimensional"]
    assert result["motif"]["start_time"]


def test_qudt_conversion_micro_to_milli_si_per_centimetre():
    assert convert_qudt_value(7_500, 1e-4, 0, 1e-1, 0) == 7.5


def test_legacy_fuseki_graph_is_normalized_to_milli_si_per_centimetre():
    rows = [
        {
            "observation": "waterlink-observation",
            "sensor": TARGET,
            "time": "2025-01-01T00:00:00Z",
            "values": "7500|0.75",
            "units": f"{MICRO_S_PER_CM}|{CANONICAL_UNIT_URI}",
        },
        {
            "observation": "waterinfo-observation",
            "sensor": UPSTREAM,
            "time": "2025-01-01T00:00:00Z",
            "values": "0.71",
            "units": CANONICAL_UNIT_URI,
        },
    ]
    normalized, report = normalize_fuseki_observations(rows)
    assert normalized[0]["result"] == 7.5
    assert normalized[1]["result"] == 7.1
    assert all(item["legacy_graph_repair"] for item in report)


def test_legacy_reader_prefers_new_correct_value_after_pipeline_rerun():
    rows = [
        {
            "observation": "waterlink-observation",
            "sensor": TARGET,
            "time": "2025-01-01T00:00:00Z",
            "values": "7500|0.75|7.5",
            "units": f"{MICRO_S_PER_CM}|{CANONICAL_UNIT_URI}",
        },
        {
            "observation": "waterinfo-observation",
            "sensor": UPSTREAM,
            "time": "2025-01-01T00:00:00Z",
            "values": "0.71|7.1",
            "units": CANONICAL_UNIT_URI,
        },
    ]
    normalized, _ = normalize_fuseki_observations(rows)
    assert normalized[0]["result"] == 7.5
    assert normalized[1]["result"] == 7.1
