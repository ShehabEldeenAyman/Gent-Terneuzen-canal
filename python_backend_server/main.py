from fastapi import FastAPI, Response,Request
from contextlib import asynccontextmanager

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

import constants
import start_preprocessing

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
#####################################################################################################
app = FastAPI()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")

    app.state.sensor_set = await start_preprocessing.identify_unique_sensors()
    app.state.final_df = await start_preprocessing.reframe_data(app.state.sensor_set)
    app.state.df_featured = await start_preprocessing.featureengineering(app.state.final_df)
    app.state.X_train, app.state.y_train, app.state.X_test, app.state.y_test = await start_preprocessing.datapreparation(app.state.df_featured)
    # app.state.model = await lightGBM_train(app.state.X_train, app.state.y_train, app.state.X_test, app.state.y_test)
    # app.state.forecast, app.state.mae, app.state.error = await lightGBM_forecast_bias(app.state.model, app.state.X_test, app.state.y_test)
    # app.state.predictions_xgb = await xgboost_train(app.state.X_train, app.state.y_train, app.state.X_test, app.state.y_test)
    # app.state.mae_xgb = await xgboost_forecast_bias(app.state.predictions_xgb, app.state.y_test)

    print("Startup complete!")
    yield # The app runs while execution is paused here
    print("Shutting down...")

app = FastAPI(lifespan=lifespan)

#####################################################################################################
@app.get("/")
async def root():
    return {"message": "Welcome to the Gent-Terneuzen Canal Sensor Data API! Available endpoints: /sensor_data, /lightGBM_forecast, /xgboost_forecast" }

@app.get("/sensor_data")
async def plot_sensor_data(request: Request):
    fig, axes = plt.subplots(nrows=4, ncols=1, figsize=(12, 10), sharex=True)

    for i, sensor in enumerate(constants.sensors):
        ax = axes[i]
        ax.plot(request.app.state.final_df.index, request.app.state.final_df[sensor], label=f"Sensor {sensor}", color=constants.colors[i])
        ax.set_ylabel("Value")
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)

    plt.suptitle("Sensor Data Analysis", fontsize=16)
    plt.xlabel("Time")
    plt.xticks(rotation=45)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    # 2. Save plot to a bytes buffer instead of plt.show()
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close() # Important: Close the plot to free up server memory

    # 3. Return the buffer as a streaming response
    return Response(content=buf.getvalue(), media_type="image/png")


@app.get("/lightGBM_forecast")
async def lightGBM_visualization(request: Request):
    app.state.model = await lightGBM_train(app.state.X_train, app.state.y_train, app.state.X_test, app.state.y_test)
    app.state.forecast, app.state.mae, app.state.error = await lightGBM_forecast_bias(app.state.model, app.state.X_test, app.state.y_test)
    # 1. Create a DataFrame for easy plotting
    results = pd.DataFrame({
        'Actual': request.app.state.y_test,
        'Forecast': request.app.state.forecast
    }, index=request.app.state.y_test.index)

    # 2. Plotting a 7-day window to see the detail
    plt.figure(figsize=(15, 7))
    plt.plot(results['Actual'].iloc[:2688], label='Ground Truth (Actual)', color='blue', alpha=0.7)
    # 672 rows = 7 days * 24 hours * 4 readings/hour
    plt.plot(results['Forecast'].iloc[:2688], label='LightGBM Forecast', color='red', linestyle='--')

    plt.title('Conductivity Forecast vs Ground Truth (Month of '' 2025)')
    plt.xlabel('Date')
    plt.ylabel('Conductivity (μS/cm)')
    plt.legend()
    plt.grid(True, alpha=0.3)

    # 2. Save plot to a bytes buffer instead of plt.show()
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close() # Important: Close the plot to free up server memory

    # 3. Return the buffer as a streaming response
    return Response(content=buf.getvalue(), media_type="image/png")

@app.get("/xgboost_forecast")
async def xgboost_visualization(request: Request):
    app.state.predictions_xgb = await xgboost_train(app.state.X_train, app.state.y_train, app.state.X_test, app.state.y_test)
    app.state.mae_xgb = await xgboost_forecast_bias(app.state.predictions_xgb, app.state.y_test)

    results_xgb = pd.DataFrame({
        'Actual':  request.app.state.y_test,
        'XGBoost_Forecast': request.app.state.predictions_xgb
    }, index=request.app.state.y_test.index)

    # 2. Plotting the 28-day window (2688 rows)
    plt.figure(figsize=(15, 7))

    # Plot Actual Data
    plt.plot(results_xgb['Actual'].iloc[:2688], 
            label='Ground Truth (Actual)', 
            color='blue', 
            alpha=0.6)

    # Plot XGBoost Forecast
    plt.plot(results_xgb['XGBoost_Forecast'].iloc[:2688], 
            label='XGBoost Forecast', 
            color='green',           # Using Green to distinguish from LightGBM's Red
            linestyle='--', 
            linewidth=1.5)

    plt.title('Conductivity Forecast vs Ground Truth (XGBoost - Sept 2025)')
    plt.xlabel('Date')
    plt.ylabel('Conductivity (μS/cm)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 2. Save plot to a bytes buffer instead of plt.show()
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close() # Important: Close the plot to free up server memory

    # 3. Return the buffer as a streaming response
    return Response(content=buf.getvalue(), media_type="image/png")

