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
from sklearn.metrics import mean_absolute_error
import lightgbm as lgb
import xgboost as xgb

async def lightGBM_train(X_train, y_train, X_test, y_test):
    model = lgb.LGBMRegressor(
        min_gain_to_split=0.0,
        n_estimators=5000,      # Increased: More trees for better learning
        learning_rate=0.01,     # Decreased: Slower, more precise learning
        num_leaves=64,         # Increased: Allows for more complex patterns
        max_depth=8,           # Limited: Prevents the trees from growing too deep
        min_data_in_leaf=20,   # Regularization: Prevents overfitting to noise (lower = more sensitive)
        feature_fraction=0.8,   # Generalization: Don't rely on all sensors at once
        n_jobs=-1,
        subsample=0.8,          # ADD: row subsampling for better generalisation
        reg_alpha=0.1,          # ADD: L1 regularisation
        reg_lambda=0.1,         # ADD: L2 regularisation
    )

    # Use early stopping to find the perfect n_estimators automatically
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        eval_metric='rmse',
        callbacks=[lgb.early_stopping(stopping_rounds=100)] 
    )
    return model

async def lightGBM_forecast_bias(model, X_test, y_test):
    forecast = model.predict(X_test)
    mae = mean_absolute_error(y_test, forecast)
    print(f"September 2025 Forecast MAE: {mae:.4f} units of conductivity")
    error = y_test - forecast
    print(f"Mean Error (Bias): {error.mean()}")
    return forecast, mae, error