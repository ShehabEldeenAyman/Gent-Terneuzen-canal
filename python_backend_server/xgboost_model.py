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

async def xgboost_train(X_train, y_train, X_test, y_test):
    dtrain = xgb.DMatrix(X_train, label=y_train)
    dtest = xgb.DMatrix(X_test, label=y_test)
    params = {
        'objective': 'reg:squarederror',
        'max_depth': 6,
        'eta': 0.01,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'colsample_bylevel': 0.8,       # ADD: also subsample per tree depth level
        'min_child_weight': 10,         # ADD: min sum of instance weight in a leaf (like min_data_in_leaf in LightGBM)
        'gamma': 0.1,                   # ADD: min loss reduction required to split (0 = no constraint)
        'alpha': 0.1,                   # ADD: L1 regularisation on weights
        'lambda': 1.5,                  # ADD: L2 regularisation on weights (default is 1)
        'eval_metric': ['rmse', 'mae'], # CHANGE: watch both so you can see error shape
        'seed': 42,                     # ADD: reproducibility
    }

    evallist = [(dtrain, 'train'), (dtest, 'eval')]

    # ADD: verbose_eval so you only print every 100 rounds instead of every round
    bst = xgb.train(
        params,
        dtrain,
        num_boost_round=5000,           # CHANGE: give it more headroom, early stopping will cut it short
        evals=evallist,
        early_stopping_rounds=100,      # CHANGE: 50 is too aggressive at lr=0.01, use 100
        verbose_eval=100,               # ADD: only log every 100 rounds
    )

    print(f"Best iteration : {bst.best_iteration}")
    print(f"Best eval MAE  : {bst.best_score:.4f}")

    predictions_xgb = bst.predict(dtest, iteration_range=(0, bst.best_iteration)) # XGBoost doesn't automatically use best_iteration on predict. Without this, it uses ALL trees including the ones after the best checkpoint.
    return predictions_xgb

async def xgboost_forecast_bias(predictions_xgb, y_test):
    mae_xgb = mean_absolute_error(y_test, predictions_xgb)
    print(f"XGBoost  MAE: {mae_xgb:.4f}")
    return mae_xgb