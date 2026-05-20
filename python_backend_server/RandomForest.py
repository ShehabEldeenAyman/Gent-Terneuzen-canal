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

async def RandomForest(X_train, y_train, X_test, y_test):
        # Initialize the Model
    # n_estimators=100 is a good start; max_depth prevents overfitting
    print("\nTraining Random Forest Regressor...")
    rf_model = RandomForestRegressor(n_estimators=200, max_depth=15, random_state=42)

    # Train
    rf_model.fit(X_train, y_train)

    # 3. Predict & Evaluate
    y_pred = rf_model.predict(X_test)

    mae  = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2   = r2_score(y_test, y_pred)
    return y_pred, mae, rmse, r2