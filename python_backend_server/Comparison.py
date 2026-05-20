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

def comparisonforecast(forecast, predictions_xgb, y_test):
    # Head to head comparison
    comparison = pd.DataFrame({
        'Actual':   y_test.values[:2688],
        'LightGBM': forecast[:2688],
        'XGBoost':  predictions_xgb[:2688]
    }, index=y_test.index[:2688]) 
    return comparison
