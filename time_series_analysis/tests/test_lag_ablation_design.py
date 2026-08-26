import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from time_series_analysis import paper_experiment_utils as utils


def assert_shared_targets_and_local_features(test_case, datasets):
    expected = [f"lag_{hours}h" for hours in utils.LAG_ABLATION_HOURS]
    expected.append(utils.LAG_ABLATION_CONTROL)
    test_case.assertEqual(list(datasets), expected)

    reference = datasets[expected[0]]
    for condition in expected:
        dataset = datasets[condition]
        for split_name in ("train", "validation", "test"):
            split = dataset.splits[split_name]
            reference_split = reference.splits[split_name]
            test_case.assertEqual(split.X.shape, reference_split.X.shape)
            test_case.assertEqual(split.X.shape[-1], 4)
            np.testing.assert_array_equal(
                split.forecast_times, reference_split.forecast_times
            )
            np.testing.assert_allclose(split.y_delta, reference_split.y_delta)
            np.testing.assert_allclose(split.baseline, reference_split.baseline)
            np.testing.assert_allclose(split.X[..., :3], reference_split.X[..., :3])


def assert_shuffled_control_preserves_upstream_distribution(test_case, datasets):
    base = datasets["lag_42h"]
    control = datasets[utils.LAG_ABLATION_CONTROL]
    for split_name in ("train", "validation", "test"):
        base_upstream = base.splits[split_name].X[..., -1]
        control_upstream = control.splits[split_name].X[..., -1]
        test_case.assertFalse(np.allclose(base_upstream, control_upstream))
        np.testing.assert_allclose(
            np.sort(base_upstream.ravel()), np.sort(control_upstream.ravel())
        )


class LagAblationDesignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        index = pd.date_range(
            "2025-01-01", "2025-02-28 23:45:00", freq="15min", tz="UTC"
        )
        step = np.arange(len(index), dtype=np.float32)
        cls.data = pd.DataFrame(
            {
                sensor: (
                    1.0
                    + 0.15 * np.sin(step / (25.0 + sensor_index * 3.0))
                    + 0.01 * sensor_index
                    + 0.0001 * step
                )
                for sensor_index, sensor in enumerate(utils.SENSOR_NAMES)
            },
            index=index,
        )

    def setUp(self):
        periods = {
            "train": ("2025-01-04", "2025-01-31 23:59:59"),
            "validation": ("2025-02-01", "2025-02-10 23:59:59"),
            "test": ("2025-02-11", "2025-02-20 23:59:59"),
        }
        self.patchers = [
            patch.object(utils, "TRAIN_PERIOD", periods["train"]),
            patch.object(utils, "VALIDATION_PERIOD", periods["validation"]),
            patch.object(utils, "TEST_PERIOD", periods["test"]),
            patch.object(utils, "SPLIT_PERIODS", periods),
        ]
        for patcher in self.patchers:
            patcher.start()

    def tearDown(self):
        for patcher in reversed(self.patchers):
            patcher.stop()

    def test_classical_lag_ablation_is_fixed_dimensional(self):
        datasets = utils.build_classical_lag_ablation_datasets(
            self.data, shuffle_seed=42
        )
        assert_shared_targets_and_local_features(self, datasets)
        assert_shuffled_control_preserves_upstream_distribution(self, datasets)
        self.assertEqual(datasets["lag_24h"].splits["train"].X.ndim, 2)

    def test_neural_lag_ablation_is_fixed_dimensional(self):
        datasets = utils.build_neural_lag_ablation_datasets(
            self.data, sequence_hours=42, shuffle_seed=42
        )
        assert_shared_targets_and_local_features(self, datasets)
        assert_shuffled_control_preserves_upstream_distribution(self, datasets)
        train = datasets["lag_24h"].splits["train"].X
        self.assertEqual(train.ndim, 3)
        self.assertEqual(train.shape[1:], (42 * utils.STEPS_PER_HOUR, 4))

    def test_lag_ablation_requires_42_hour_control_base(self):
        with self.assertRaisesRegex(ValueError, "42-hour condition is required"):
            utils.build_classical_lag_ablation_datasets(
                self.data, lag_hours=(24, 36, 48, 60)
            )


if __name__ == "__main__":
    unittest.main()
