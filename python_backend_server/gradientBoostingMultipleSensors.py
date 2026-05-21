from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.multioutput import MultiOutputRegressor
import requests
from rdflib import Graph, URIRef, Literal, Namespace
import io
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Agg') # Non-interactive backend (required for servers)
from statsmodels.graphics.tsaplots import plot_acf
from statsmodels.tsa.stattools import acf
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import lightgbm as lgb
import xgboost as xgb
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score

import constants

async def gradientBoostingMultipleSensors(final_df):
 
    data = final_df.copy().sort_index()
 
 
    # Fill gaps so a single dropped sensor doesn't discard entire rows
    data[constants.sensors] = data[constants.sensors].ffill().bfill()
 
    # 1. Create Historical Lag Features for ALL 4 Sensors
    n_lags = 8  # 2 hours of memory (8 × 15 min)
    feature_cols = []
    for sensor in constants.sensors:
        for lag in range(1, n_lags + 1):
            col_name = f'{sensor}_lag_{lag}'
            data[col_name] = data[sensor].shift(lag)
            feature_cols.append(col_name)
 
    # Add time-based features to help the model learn cyclical patterns
    data['hour'] = data.index.hour
    data['day_of_week'] = data.index.dayofweek
    data['month'] = data.index.month
    feature_cols += ['hour', 'day_of_week', 'month']
 
    # Drop the rows with NaN values created by the shift
    data = data.dropna()
 
    # X contains lags and time features; y contains current readings for ALL sensors
    X = data[feature_cols]
    y = data[constants.sensors]
 
    # 2. Chronological Train-Test Split
    # Withhold the final 24 hours (96 × 15-min steps) as the test set
    forecast_steps = 96
    X_train, X_test = X.iloc[:-forecast_steps], X.iloc[-forecast_steps:]
    y_train, y_test = y.iloc[:-forecast_steps], y.iloc[-forecast_steps:]
 
    # 3. Train the Multi-Output Gradient Boosting Model
    # MultiOutputRegressor trains one GBR per target sensor under the hood
    print("Training Multivariate Gradient Boosting Regressor (this may take a minute)...")
    base_model = GradientBoostingRegressor(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=5,
        random_state=42
    )
    multi_model = MultiOutputRegressor(base_model)
    multi_model.fit(X_train, y_train)
    print("Training Complete!")
 
    # 4. Recursive Forecasting for the next 24 hours
    # Seed the rolling history with the last n_lags known values for each sensor
    recent_history = {
        sensor: y_train[sensor].values[-n_lags:].tolist()
        for sensor in constants.sensors
    }
 
    target_forecasts = []
    future_dates = y_test.index
 
    print("Generating 24-hour multivariate forecast...")
    for i in range(forecast_steps):
 
        # A. Build lag features for all sensors
        current_features = []
        for sensor in constants.sensors:
            # Reverse so the most recent value becomes lag_1
            current_features.extend(recent_history[sensor][::-1][:n_lags])
 
        # B. Append time features for the exact step being predicted
        pred_time = future_dates[i]
        current_features.extend([pred_time.hour, pred_time.dayofweek, pred_time.month])
 
        # C. Predict all 4 sensors at once
        x_pred = np.array(current_features).reshape(1, -1)
        pred_vals = multi_model.predict(x_pred)[0]  # Shape: (4,)
 
        # D. Roll each sensor's history forward with its new prediction
        for idx, sensor in enumerate(constants.sensors):
            recent_history[sensor].append(pred_vals[idx])
            if sensor == constants.target_sensor:
                target_forecasts.append(pred_vals[idx])
 
    # Return the same shape as gradientBoosting1Sensor for drop-in compatibility
    return (
        target_forecasts,
        y_test[constants.target_sensor],
        mean_absolute_error(y_test[constants.target_sensor], target_forecasts),
        r2_score(y_test[constants.target_sensor], target_forecasts),
    )