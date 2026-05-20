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
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import lightgbm as lgb
import xgboost as xgb

import constants
import start_preprocessing
import lightGBM
import XGboost
import Ensemble
import Comparison
import RandomForest
import SupportVectorMachine
# Find the data leakage #

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
    app.state.model = await lightGBM.lightGBM_train(app.state.X_train, app.state.y_train, app.state.X_test, app.state.y_test)
    app.state.forecast, app.state.mae, app.state.error = await lightGBM.lightGBM_forecast_bias(app.state.model, app.state.X_test, app.state.y_test)
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
    app.state.predictions_xgb = await XGboost.xgboost_train(app.state.X_train, app.state.y_train, app.state.X_test, app.state.y_test)
    app.state.mae_xgb = await XGboost.xgboost_forecast_bias(app.state.predictions_xgb, app.state.y_test)

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

@app.get("/ensemble_forecast")
async def ensemble_visualization(request: Request):

    app.state.final_ensemble, app.state.mae_ensemble = Ensemble.ensemble(app.state.forecast, app.state.predictions_xgb, app.state.y_test)

    results = pd.DataFrame({
        'Actual':   app.state.y_test.values[:2688],
        'Forecast': app.state.final_ensemble[:2688]
    }, index=app.state.y_test.index[:2688])

    plt.figure(figsize=(15, 7))
    plt.plot(results['Actual'],   label='Ground Truth (Actual)', color='blue', alpha=0.7)
    plt.plot(results['Forecast'], label='LightGBM Forecast',     color='red',  linestyle='--')

    plt.title('Conductivity Forecast vs Ground Truth')
    plt.xlabel('Date')
    plt.ylabel('Conductivity (μS/cm)')
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # 2. Save plot to a bytes buffer instead of plt.show()
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close() # Important: Close the plot to free up server memory

    # 3. Return the buffer as a streaming response
    return Response(content=buf.getvalue(), media_type="image/png")

@app.get("/random_forest")
async def random_forest_visualization(request: Request):

    app.state.predictions_rf, app.state.mae_rf, app.state.rmse_rf, app.state.r2_rf = await RandomForest.RandomForest(app.state.X_train, app.state.y_train, app.state.X_test, app.state.y_test)

    print(f"\n{'Metric':<10} {'Value':>10}")
    print("-" * 22)
    print(f"{'MAE':<10} {app.state.mae_rf:>10.4f}")
    print(f"{'RMSE':<10} {app.state.rmse_rf:>10.4f}")
    print(f"{'R²':<10} {app.state.r2_rf:>10.4f}")

    # 4. Actual vs Predicted plot
    fig, ax = plt.subplots(figsize=(14, 4))
    ax.plot(app.state.y_test.index, app.state.y_test.values,  label='Actual',    alpha=0.8)
    ax.plot(app.state.y_test.index, app.state.predictions_rf,label='Predicted', alpha=0.8, linestyle='--')
    ax.set_title(f'Random Forest – Actual vs Predicted: {constants.target_sensor}')
    ax.set_xlabel('Time')
    ax.legend()
    plt.tight_layout()
    
    # 2. Save plot to a bytes buffer instead of plt.show()
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close() # Important: Close the plot to free up server memory

    # 3. Return the buffer as a streaming response
    return Response(content=buf.getvalue(), media_type="image/png")

@app.get("/SVR")
async def SVR_visualization(request: Request):

    y_pred, mae, rmse, r2 = await SupportVectorMachine.SupportVectorMachine(app.state.X_train, app.state.y_train, app.state.X_test, app.state.y_test)

    print(f"R-squared Accuracy: {r2:.4f}")
    # 3. Visualization
    plt.figure(figsize=(12, 6))

    # Use the index if your timestamp is the index, 
    # or use data['unixtime'] if you want to see the raw numbers.
    # If you have a human-readable column, use that here:
    #time_axis = data['unixtime'] 

    plt.plot(app.state.y_test.index, app.state.y_test.values, label='Actual Sensor (289429042)', color='blue', alpha=0.6, linewidth=2)
    plt.plot(app.state.y_test.index, y_pred, label='SVR Prediction', color='red', linestyle='--', alpha=0.9)

    plt.title('Canal Water Conductivity: Actual vs. SVR Prediction')
    plt.xlabel('Time (Unix Format)')
    plt.ylabel('Conductivity (µS/cm)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    # 2. Save plot to a bytes buffer instead of plt.show()
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close() # Important: Close the plot to free up server memory

    # 3. Return the buffer as a streaming response
    return Response(content=buf.getvalue(), media_type="image/png")



#####################################################################################################
@app.get("/comparison_forecast")
async def comparison_visualization(request: Request):
    results = Comparison.comparisonforecast(app.state.forecast, app.state.predictions_xgb, app.state.y_test)

    plt.figure(figsize=(15, 7))
    plt.plot(results['Actual'],   label='Ground Truth (Actual)', color='blue', alpha=0.7)
    plt.plot(results['LightGBM'], label='LightGBM Forecast',     color='red',  linestyle='--')
    plt.plot(results['XGBoost'],  label='XGBoost Forecast',      color='green', linestyle='--')

    plt.title('Conductivity Forecast vs Ground Truth')
    plt.xlabel('Date')
    plt.ylabel('Conductivity (μS/cm)')
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # 2. Save plot to a bytes buffer instead of plt.show()
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close() # Important: Close the plot to free up server memory

    # 3. Return the buffer as a streaming response
    return Response(content=buf.getvalue(), media_type="image/png")
