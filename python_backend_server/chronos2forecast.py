import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from chronos import Chronos2Pipeline

async def chronos2forecast(chronos_df):
    pipeline = Chronos2Pipeline.from_pretrained("amazon/chronos-2", device_map="cpu")
    prediction_length = 3
    forecast_df = pipeline.predict_df(
    df=chronos_df,
    prediction_length=96,           # e.g. 24h at 15-min intervals
    id_column="item_id",
    timestamp_column="timestamp",
    target="target",
    quantile_levels=[0.1, 0.5, 0.9]
)
    print(forecast_df.head())

    return forecast_df

