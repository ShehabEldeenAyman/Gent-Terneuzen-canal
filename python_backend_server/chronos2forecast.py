import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from chronos import Chronos2Pipeline

async def chronos2forecast(chronos_df):
    pipeline = Chronos2Pipeline.from_pretrained("amazon/chronos-2", device_map="cpu")
    
    # 1. Ensure timestamp is actually datetime inside the pipeline function
    chronos_df = chronos_df.copy()
    chronos_df["timestamp"] = pd.to_datetime(chronos_df["timestamp"])
    
    # 2. Subtract 3 days using a clear Pandas Timedelta instead of raw seconds math
    cutoff_time = chronos_df["timestamp"].max() - pd.Timedelta(days=3)
    filtered_df = chronos_df[chronos_df["timestamp"] <= cutoff_time]
    
    prediction_length = 96 # 24h at 15-min intervals
    
    forecast_df = pipeline.predict_df(
        df=filtered_df,
        prediction_length=prediction_length,
        id_column="item_id",
        timestamp_column="timestamp",
        target="target",
        quantile_levels=[0.1, 0.5, 0.9]
    )
    
    print(forecast_df.head())
    return forecast_df