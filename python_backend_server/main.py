from fastapi import FastAPI, Response,Request
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

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

import matplotlib.dates as mdates

import constants
import start_preprocessing
import lightGBM
import xgboost_model  
import Ensemble
import Comparison
import RandomForest
import SupportVectorMachine
import gradientBoosting1Sensor
import gradientBoostingMultipleSensors
import chronos2forecast
# Find the data leakage #

#####################################################################################################
app = FastAPI()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")

    app.state.sensor_set = await start_preprocessing.identify_unique_sensors()
    app.state.final_df = await start_preprocessing.reframe_data(app.state.sensor_set, after="2025-01-01", before="2025-12-31")
    #app.state.df_featured = await start_preprocessing.featureengineering(app.state.final_df)
    #app.state.X_train, app.state.y_train, app.state.X_test, app.state.y_test = await start_preprocessing.datapreparation(app.state.df_featured)

    # app.state.X_train_raw, app.state.y_train_raw, app.state.X_test_raw, app.state.y_test_raw = await start_preprocessing.datapreparation(app.state.final_df)
    # app.state.X_train, app.state.y_train = await start_preprocessing.featureengineering(app.state.X_train_raw, app.state.y_train_raw, fit=True)
    # app.state.X_test,  app.state.y_test  = await start_preprocessing.featureengineering(app.state.X_test_raw,  app.state.y_test_raw,  fit=False)

    # NEW
    train_df, test_df = await start_preprocessing.datapreparation(app.state.final_df)

    app.state.X_train, app.state.y_train = await start_preprocessing.featureengineering(train_df, fit=True)

    # Prepend last 2880 rows of train to test so lag features at the boundary aren't NaN
    max_lag = 2881
    context_df = pd.concat([train_df.iloc[-max_lag:], test_df])
    X_test_ctx, y_test_ctx = await start_preprocessing.featureengineering(context_df, fit=False)
    # Trim off the prepended context rows, keep only true test period
    app.state.X_test = X_test_ctx[X_test_ctx.index >= test_df.index[0]]
    app.state.y_test = y_test_ctx[y_test_ctx.index >= test_df.index[0]]

    # app.state.model = await lightGBM_train(app.state.X_train, app.state.y_train, app.state.X_test, app.state.y_test)
    # app.state.forecast, app.state.mae, app.state.error = await lightGBM_forecast_bias(app.state.model, app.state.X_test, app.state.y_test)
    # app.state.predictions_xgb = await xgboost_train(app.state.X_train, app.state.y_train, app.state.X_test, app.state.y_test)
    # app.state.mae_xgb = await xgboost_forecast_bias(app.state.predictions_xgb, app.state.y_test)

    app.state.chronos_df = await start_preprocessing.prepare_for_chronos(app.state.final_df)
    app.state.chronos_df_no_avg = await start_preprocessing.prepare_for_chronos_no_avg(app.state.final_df)
    print("Startup complete!")
    yield # The app runs while execution is paused here
    print("Shutting down...")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
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
    plt.plot(results['Actual'], label='Ground Truth (Actual)', color='blue', alpha=0.7)
    plt.plot(results['Forecast'], label='LightGBM Forecast', color='red', linestyle='--')
    plt.title('LightGBM')
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
    app.state.predictions_xgb = await xgboost_model.xgboost_train(app.state.X_train, app.state.y_train, app.state.X_test, app.state.y_test)
    app.state.mae_xgb = await xgboost_model.xgboost_forecast_bias(app.state.predictions_xgb, app.state.y_test)

    results_xgb = pd.DataFrame({
        'Actual':  request.app.state.y_test,
        'XGBoost_Forecast': request.app.state.predictions_xgb
    }, index=request.app.state.y_test.index)

    # 2. Plotting the 28-day window (2688 rows)
    plt.figure(figsize=(15, 7))

    # Plot Actual Data
    plt.plot(results_xgb['Actual'], 
            label='Ground Truth (Actual)', 
            color='blue', 
            alpha=0.6)

    # Plot XGBoost Forecast
    plt.plot(results_xgb['XGBoost_Forecast'], 
            label='XGBoost Forecast', 
            color='red',           # Using Green to distinguish from LightGBM's Red
            linestyle='--', 
            linewidth=1.5)

    plt.title('XGBoost')
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
    # 1. Fallback: Generate LightGBM forecast if missing
    if not hasattr(request.app.state, 'forecast'):
        request.app.state.model = await lightGBM.lightGBM_train(
            request.app.state.X_train, request.app.state.y_train, request.app.state.X_test, request.app.state.y_test
        )
        request.app.state.forecast, request.app.state.mae, request.app.state.error = await lightGBM.lightGBM_forecast_bias(
            request.app.state.model, request.app.state.X_test, request.app.state.y_test
        )

    # 2. Fallback: Generate XGBoost forecast if missing
    if not hasattr(request.app.state, 'predictions_xgb'):
        request.app.state.predictions_xgb = await xgboost_model.xgboost_train(
            request.app.state.X_train, request.app.state.y_train, request.app.state.X_test, request.app.state.y_test
        )

    # 3. Safe to compute ensemble now
    request.app.state.final_ensemble, request.app.state.mae_ensemble = Ensemble.ensemble(
        request.app.state.forecast, request.app.state.predictions_xgb, request.app.state.y_test
    )

    results = pd.DataFrame({
        'Actual':   request.app.state.y_test.values[:2688],
        'Forecast': request.app.state.final_ensemble[:2688]
    }, index=request.app.state.y_test.index[:2688])

    plt.figure(figsize=(15, 7))
    plt.plot(results['Actual'],   label='Ground Truth (Actual)', color='blue', alpha=0.7)
    plt.plot(results['Forecast'], label='Ensemble Forecast',     color='red',  linestyle='--') # Switched to purple to denote combined forecast

    plt.title('Ensemble Forecast (LightGBM + XGBoost)')
    plt.xlabel('Date')
    plt.ylabel('Conductivity (μS/cm)')
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()

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
    ax.plot(app.state.y_test.index, app.state.y_test.values,  label='Actual',    alpha=0.8,color='blue')
    ax.plot(app.state.y_test.index, app.state.predictions_rf,label='Predicted', alpha=0.8, linestyle='--', color='red')
    ax.set_title(f'Random Forest')
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

    plt.title('SVR')
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

# @app.get("/gradient_boosting_1_sensor")
# async def GradientBoosting1Sensor_visualization(request: Request):

#     forecasts, gb_y_test, mae, r2 = await gradientBoosting1Sensor.GradientBoosting1Sensor(request.app.state.final_df)

#     print(f"\n24-Hour Forecast Accuracy:")
#     print(f"MAE:  {mae:.2f} µS/cm")
#     print(f"R²:   {r2:.4f}")

#     plt.figure(figsize=(14, 5))
#     plt.plot(gb_y_test.index, gb_y_test.values, label='Actual Conductivity', color='blue', linewidth=2, alpha=0.7)
#     plt.plot(gb_y_test.index, forecasts, label='Gradient Boosting Forecast', color='red', linestyle='--', linewidth=2)
#     plt.title(f'24-Hour Future Forecast for Sensor {constants.target_sensor}')
#     plt.xlabel('Time')
#     plt.ylabel('Conductivity (µS/cm)')
#     plt.legend()
#     plt.grid(True, alpha=0.3)
#     plt.tight_layout()
#     # 2. Save plot to a bytes buffer instead of plt.show()
#     buf = io.BytesIO()
#     plt.savefig(buf, format="png")
#     buf.seek(0)
#     plt.close() # Important: Close the plot to free up server memory

#     # 3. Return the buffer as a streaming response
#     return Response(content=buf.getvalue(), media_type="image/png")

# @app.get("/gradient_boosting_multiple_sensors")
# async def GradientBoostingMultipleSensors_visualization(request: Request):

#     target_forecasts, y_test, mae, r2 = await gradientBoostingMultipleSensors.gradientBoostingMultipleSensors(request.app.state.final_df)
#     print(f"\nMultivariate 24-Hour Forecast Accuracy (Sensor {constants.target_sensor}):")
#     print(f"MAE:  {mae:.2f} µS/cm")
#     print(f"R²:   {r2:.4f}")

#     plt.figure(figsize=(14, 5))
#     plt.plot(y_test.index, y_test[constants.target_sensor].values, label='Actual Conductivity', color='blue', linewidth=2, alpha=0.7)
#     plt.plot(y_test.index, target_forecasts, label='Multivariate GB Forecast', color='red', linestyle='--', linewidth=2)
#     plt.title(f'24-Hour Future Forecast for Sensor {constants.target_sensor} (Using All Sensor Data)')
#     plt.xlabel('Time')
#     plt.ylabel('Conductivity (µS/cm)')
#     plt.legend()
#     plt.grid(True, alpha=0.3)
#     plt.tight_layout()
# # 2. Save plot to a bytes buffer instead of plt.show()
#     buf = io.BytesIO()
#     plt.savefig(buf, format="png")
#     buf.seek(0)
#     plt.close() # Important: Close the plot to free up server memory
#     return Response(content=buf.getvalue(), media_type="image/png")

#####################################################################################################
@app.get("/comparison_forecast")
async def comparison_visualization(request: Request):
    # 1. Fallback: Generate LightGBM forecast if missing
    if not hasattr(request.app.state, 'forecast'):
        request.app.state.model = await lightGBM.lightGBM_train(
            request.app.state.X_train, request.app.state.y_train, request.app.state.X_test, request.app.state.y_test
        )
        request.app.state.forecast, request.app.state.mae, request.app.state.error = await lightGBM.lightGBM_forecast_bias(
            request.app.state.model, request.app.state.X_test, request.app.state.y_test
        )

    # 2. Fallback: Generate XGBoost forecast if missing
    if not hasattr(request.app.state, 'predictions_xgb'):
        request.app.state.predictions_xgb = await xgboost_model.xgboost_train(
            request.app.state.X_train, request.app.state.y_train, request.app.state.X_test, request.app.state.y_test
        )
        request.app.state.mae_xgb = await xgboost_model.xgboost_forecast_bias(
            request.app.state.predictions_xgb, request.app.state.y_test
        )

    # 3. Fallback: Generate Random Forest forecast if missing
    if not hasattr(request.app.state, 'predictions_rf'):
        request.app.state.predictions_rf, request.app.state.mae_rf, request.app.state.rmse_rf, request.app.state.r2_rf = await RandomForest.RandomForest(
            request.app.state.X_train, request.app.state.y_train, request.app.state.X_test, request.app.state.y_test
        )

    # 4. Fallback: Generate SVR forecast if missing
    if not hasattr(request.app.state, 'predictions_svr'):
        request.app.state.predictions_svr, request.app.state.mae_svr, request.app.state.rmse_svr, request.app.state.r2_svr = await SupportVectorMachine.SupportVectorMachine(
            request.app.state.X_train, request.app.state.y_train, request.app.state.X_test, request.app.state.y_test
        )

    # 5. Build data frame combining all models to easily map lines
    results = pd.DataFrame({
        'Actual':       request.app.state.y_test,
        'LightGBM':     request.app.state.forecast,
        'XGBoost':      request.app.state.predictions_xgb,
        'RandomForest': request.app.state.predictions_rf,
        'SVR':          request.app.state.predictions_svr
    }, index=request.app.state.y_test.index)

    # 6. Generate Multi-Model Comparison Plot
    plt.figure(figsize=(15, 7))
    plt.plot(results['Actual'],       label='Ground Truth (Actual)',  color='blue',   alpha=0.7, linewidth=2)
    plt.plot(results['LightGBM'],     label='LightGBM Forecast',      color='red',    linestyle='--')
    plt.plot(results['XGBoost'],      label='XGBoost Forecast',       color='green',  linestyle='--')
    plt.plot(results['RandomForest'], label='Random Forest Forecast', color='orange', linestyle='--')
    plt.plot(results['SVR'],          label='SVR Forecast',           color='purple', linestyle='--')

    plt.title('Multi-Model Conductivity Forecast Comparison')
    plt.xlabel('Date')
    plt.ylabel('Conductivity (μS/cm)')
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()

    return Response(content=buf.getvalue(), media_type="image/png")
#####################################################################################################
@app.get("/chronos2forecast")
async def chronos2forecast_visualization(request: Request):
    # 1. Get the historical averaged dataframe from the app state
    df = request.app.state.chronos_df.copy()
    
    # 2. Run the forecast pipeline
    forecast_df = await chronos2forecast.chronos2forecast(df, forecast_as_of="2025-12-30")

    # 3. Ensure timestamps are in datetime format to prevent math errors
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    forecast_df["timestamp"] = pd.to_datetime(forecast_df["timestamp"])
    
    # 4. Explicitly sort chronologically to guarantee continuous lines without overlapping loops
    df = df.sort_values("timestamp")
    forecast_df = forecast_df.sort_values("timestamp")
    
    # 5. Use the start of the forecast as our anchor point
    forecast_start_time = forecast_df["timestamp"].min()
    
    # --- VISUALIZATION TIME FRAME WINDOW ---
    history_start = pd.Timestamp("2025-12-14", tz="UTC")
    recent_history_df = df[df["timestamp"] >= history_start]
    # ---------------------------------------

    # 6. Plotting the results
    fig, ax = plt.subplots(figsize=(26, 6))

    # Plot the historical window of the average values
    ax.plot(
        recent_history_df["timestamp"], 
        recent_history_df["target"], 
        label="Historical Data (4-Sensor Avg)", 
        color="black", 
        linewidth=1.5
    )

    # Plot forecast median
    ax.plot(
        forecast_df["timestamp"], 
        forecast_df["0.5"], 
        label="Chronos-2 Forecast (Median)", 
        color="blue", 
        linestyle="--", 
        linewidth=2    
    )

    # Plot prediction interval (80% confidence uncertainty band)
    ax.fill_between(
        forecast_df["timestamp"], 
        forecast_df["0.1"], 
        forecast_df["0.9"], 
        alpha=0.2, 
        color="blue", 
        label="80% Prediction Interval"
    )

    # 7. Cleaner x-axis: one label per day, noon marked with a minor tick only
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))   # e.g. "Dec 14"
    ax.xaxis.set_minor_locator(mdates.HourLocator(byhour=[12]))   # tick at noon, no label

    ax.grid(True, which='major', linestyle=':', alpha=0.6)
    ax.grid(True, which='minor', linestyle=':', alpha=0.25)       # subtle noon gridline

    plt.xticks(rotation=45, ha='right')

    # 8. Add chart details
    plt.title("Chronos-2 Forecast", fontsize=14, fontweight='bold')
    plt.xlabel("Date & Time", fontsize=12)
    plt.ylabel("Averaged Conductivity", fontsize=12)
    plt.legend(loc="upper left", fontsize=10)
    plt.tight_layout()
    
    # 9. Save plot to an in-memory bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=100)
    buf.seek(0)
    plt.close(fig)

    # 10. Return the buffer as a streaming image response
    return Response(content=buf.getvalue(), media_type="image/png")


@app.get("/chronos2forecast_no_avg")
async def chronos2forecast_visualization(request: Request):
    # 1. Get the historical averaged dataframe from the app state
    df = request.app.state.chronos_df_no_avg.copy()
    
    # 2. Run the forecast pipeline
    forecast_df = await chronos2forecast.chronos2forecast(df)

    # 3. Ensure timestamps are in datetime format to prevent math errors
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    forecast_df["timestamp"] = pd.to_datetime(forecast_df["timestamp"])
    
    # 4. Explicitly sort chronologically to guarantee continuous lines without overlapping loops
    df = df.sort_values("timestamp")
    forecast_df = forecast_df.sort_values("timestamp")
    
    # 5. Use the start of the forecast as our anchor point
    forecast_start_time = forecast_df["timestamp"].min()
    
    # --- VISUALIZATION TIME FRAME WINDOW ---
    # We pull the history close (last 3 days) so it doesn't squash the 24h prediction window
    history_lookback_time = forecast_start_time - pd.Timedelta(days=3)
    
    # Filter historical data to only include this zoomed-in timeframe
    recent_history_df = df[df["timestamp"] >= history_lookback_time]
    # ---------------------------------------

    # 6. Plotting the results
    # We increase the width to 16 inches to give the forecasting section horizontal breathing room
    fig, ax = plt.subplots(figsize=(16, 6))

    # Plot the 3-day historical window of the average values
    ax.plot(
        recent_history_df["timestamp"], 
        recent_history_df["target"], 
        label="Historical Data (4-Sensor Avg)", 
        color="black", 
        linewidth=1.5
    )

    # Plot forecast median
    ax.plot(
        forecast_df["timestamp"], 
        forecast_df["0.5"], 
        label="Chronos-2 Forecast (Median)", 
        color="blue", 
        linestyle="--", 
        linewidth=2    
    )

    # Plot prediction interval (80% confidence uncertainty band)
    ax.fill_between(
        forecast_df["timestamp"], 
        forecast_df["0.1"], 
        forecast_df["0.9"], 
        alpha=0.2, 
        color="blue", 
        label="80% Prediction Interval"
    )

    # 7. Formatting X-Axis Dates so they remain legible and well-spaced
    # Force a tick mark to appear at 12-hour intervals across the 4-day span (3 days history + 1 day forecast)
    ax.xaxis.set_major_locator(mdates.HourLocator(byhour=[0, 12]))  
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M')) 
    
    # Clean up labels: rotate 30 degrees and align their right side to the tick marks
    plt.xticks(rotation=30, ha='right')  

    # 8. Add chart details
    plt.title("Chronos-2 Forecast (Zoomed High-Resolution View)", fontsize=14, fontweight='bold')
    plt.xlabel("Date & Time", fontsize=12)
    plt.ylabel("Averaged Conductivity", fontsize=12)
    plt.legend(loc="upper left", fontsize=10)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout() # Prevents labels from getting clipped off at the bottom edges
    
    # 9. Save plot to an in-memory bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=100)
    buf.seek(0)
    plt.close(fig) # Explicitly clear server memory

    # 10. Return the buffer as a streaming image response
    return Response(content=buf.getvalue(), media_type="image/png")