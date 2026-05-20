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

async def GradientBoosting1Sensor(final_df):

    data = final_df.copy().sort_index()
    # We will focus on predicting one target sensor for the next 24 hours
    target_sensor = '289429042'


    # Create historical "Lag" features for the target sensor 
    # use the past 2 hours of data (8 steps of 15 minutes) as memory
    n_lags = 8
    for lag in range(1, n_lags + 1):
        data[f'lag_{lag}'] = data[target_sensor].shift(lag)

    # Add time-based features to help the model learn cyclical patterns
    data['hour'] = data.index.hour
    data['day_of_week'] = data.index.dayofweek
    data['month'] = data.index.month

    # Drop the rows with NaN values created by the shift
    data = data.dropna()

    # Define our features (X) and target (y)
    feature_cols = [f'lag_{i}' for i in range(1, n_lags + 1)] + ['hour', 'day_of_week', 'month']
    X = data[feature_cols]
    y = data[target_sensor]

    # 2. Chronological Train-Test Split
    # To validate a 24-hour forecast, we withhold the final 24 hours (96 steps) as our test set
    forecast_steps = 96 
    X_train, X_test = X.iloc[:-forecast_steps], X.iloc[-forecast_steps:]
    y_train, y_test = y.iloc[:-forecast_steps], y.iloc[-forecast_steps:]

    # 3. Train the Gradient Boosting Model
    print("Training Gradient Boosting Regressor (this may take a moment)...")
    gb_model = GradientBoostingRegressor(
        n_estimators=150, 
        learning_rate=0.1, 
        max_depth=5, 
        random_state=42
    )
    gb_model.fit(X_train, y_train)
    print("Training Complete!")

    # 4. Recursive Forecasting for the next 24 hours
    # We extract the very last known 2 hours of data from our training set to seed the forecast
    recent_history = y_train.values[-n_lags:].tolist() 
    forecasts = []
    future_dates = y_test.index 

    print("Generating 24-hour forecast...")
    for i in range(forecast_steps):
        # Construct the lag features from our rolling history
        # [::-1] reverses the list so the most recent prediction becomes lag_1
        current_lag_features = recent_history[::-1][:n_lags]
        
        # Extract the datetime features for the exact future time we are predicting
        pred_time = future_dates[i]
        time_features = [pred_time.hour, pred_time.dayofweek, pred_time.month]
        
        # Combine lags and time features into a single row for prediction
        x_pred = pd.DataFrame([current_lag_features + time_features], columns=feature_cols)

        
        # Predict the next 15-minute step
        pred_val = gb_model.predict(x_pred)[0]
        forecasts.append(pred_val)
        
        # Append the new prediction to our history so we can use it to predict the step after that
        recent_history.append(pred_val)

    return (
    forecasts,
    y_test,                            # ← add this
    mean_absolute_error(y_test, forecasts),
    r2_score(y_test, forecasts)
)