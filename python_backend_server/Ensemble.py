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

def ensemble(forecast, predictions_xgb, y_test):
    final_ensemble = (forecast + predictions_xgb) / 2
    mae_ensemble = mean_absolute_error(y_test, final_ensemble)
    print(f"Final Ensemble MAE: {mae_ensemble:.4f}")
    return final_ensemble, mae_ensemble    
