import unittest

import numpy as np
import pandas as pd

from time_series_analysis import paper_experiment_utils as utils


class ForecastContractTests(unittest.TestCase):
    def test_72_hour_horizon_and_requested_skill_marks(self):
        self.assertEqual(utils.FORECAST_HOURS, 72)
        self.assertEqual(utils.FORECAST_STEPS, 288)
        self.assertEqual(utils.EVALUATION_HOURS, (4, 8, 16, 24, 48))

        samples = 5
        future_delta = np.linspace(
            0.01, 1.0, utils.FORECAST_STEPS, dtype=np.float32
        )
        y_delta = np.stack(
            [(1.0 + 0.1 * sample) * future_delta for sample in range(samples)]
        )
        split = utils.SplitData(
            X=np.zeros((samples, 4), dtype=np.float32),
            y_delta=y_delta,
            baseline=np.ones(samples, dtype=np.float32),
            forecast_times=pd.date_range(
                "2025-09-04", periods=samples, freq="15min", tz="UTC"
            ),
        )

        rows, horizons, predictions = utils.evaluation_rows(
            "test model", "manual_42h", split, 0.5 * y_delta
        )
        scopes = {row["Scope"] for row in rows}
        self.assertTrue(
            {f"{hours}-hour mark" for hours in utils.EVALUATION_HOURS}.issubset(
                scopes
            )
        )
        self.assertEqual(len(horizons), utils.FORECAST_STEPS)
        self.assertEqual(horizons["Lead hours"].iloc[-1], 72.0)
        self.assertEqual(len(predictions), samples)


if __name__ == "__main__":
    unittest.main()
