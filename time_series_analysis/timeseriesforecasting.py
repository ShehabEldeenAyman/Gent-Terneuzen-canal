import requests
from rdflib import Graph, URIRef, Literal, Namespace
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.graphics.tsaplots import plot_acf
from statsmodels.tsa.stattools import acf
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
import lightgbm as lgb
import xgboost as xgb


#VIRTUOSO_URL = "http://localhost:8890/sparql-graph-crud"
VIRTUOSO_URL = "http://localhost:8890/sparql"
GRAPH_URI = "http://example.com/Gent-Terneuzen"
USERNAME = "dba"
PASSWORD = "dba"
AUTH  = (USERNAME,PASSWORD)

params  = {'graph': GRAPH_URI}
headers = {'Accept': 'text/turtle'}

sensors = ['289435042', '289423042', '289429042', '289441042']
colors  = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']

target_sensor = '289441042'

def identify_unique_sensors():
    sensor_set = set()

    sensor_query = f"""
        PREFIX sosa: <http://www.w3.org/ns/sosa/>
        SELECT DISTINCT ?sensor
        WHERE {{
            GRAPH <{GRAPH_URI}> {{
                ?obs a sosa:Observation ;
                    sosa:madeBySensor ?sensor .
            }}
        }}
        """
    res = requests.get(VIRTUOSO_URL, params={'query': sensor_query, 'format': 'application/sparql-results+json'})
    if res.status_code != 200:
        print(f"Error: {res.status_code}")
        print("Response:", res.text)
    else:
        print("Unique sensors identified successfully!")

    data     = res.json()
    bindings = data['results']['bindings']
    for row in bindings:
        sensor_set.add(row['sensor']['value'])

    print(f"Added {len(sensor_set)} unique sensors to the set.")
    print("Sensors:", sensor_set)
    return sensor_set


def reframe_data(sensor_set):
    final_df = pd.DataFrame()
    print("Fetching and pivoting sensor data...")

    for sensor_uri in sensor_set:
        column_name = sensor_uri.split('/')[-1]
        query = f"""
            PREFIX sosa: <http://www.w3.org/ns/sosa/>
            PREFIX ex: <http://example.com/attributes/>
            SELECT ?time ?value ?unixtime
            WHERE {{
                GRAPH <{GRAPH_URI}> {{
                    ?obs a sosa:Observation ;
                        sosa:resultTime ?time ;
                        sosa:hasSimpleResult ?value ;
                        ex:unixTimestamp ?unixtime ;
                        sosa:madeBySensor <{sensor_uri}> .
                }}
            }}
        """
        res = requests.get(VIRTUOSO_URL, params={'query': query, 'format': 'application/sparql-results+json'})
        if res.status_code == 200:
            bindings = res.json()['results']['bindings']
            temp_data = [
                {'time': row['time']['value'], column_name: float(row['value']['value']),
                'unixtime': int(row['unixtime']['value'])}
                for row in bindings
            ]
            temp_df = pd.DataFrame(temp_data)
            if not temp_df.empty:
                temp_df['time'] = pd.to_datetime(temp_df['time'])
                if final_df.empty:
                    final_df = temp_df
                else:
                    final_df = pd.merge(final_df, temp_df, on=['time', 'unixtime'], how='outer')
                print(f"Added column for sensor: {column_name}")

    final_df = final_df.sort_values('time').set_index('time')
    print("Finished!")
    print(final_df.head())
    return final_df

def plot_sensor_data(final_df):
    fig, axes = plt.subplots(nrows=4, ncols=1, figsize=(12, 10), sharex=True)

    for i, sensor in enumerate(sensors):
        ax = axes[i]
        ax.plot(final_df.index, final_df[sensor], label=f"Sensor {sensor}", color=colors[i])
        ax.set_ylabel("Value")
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)

    plt.suptitle("Sensor Data Analysis", fontsize=16)
    plt.xlabel("Time")
    plt.xticks(rotation=45)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show(block=False)
    plt.pause(0.1) # Gives the GUI time to render

#####################################################################################################
def featureengineering(final_df):
    data = final_df.copy()
    

    # 1. Time-based features (Seasonality)
    data['hour'] = data.index.hour
    data['day_of_week'] = data.index.dayofweek
    data['month'] = data.index.month


    # 2. Lag features for the TARGET (Sensor 4)
        # We look back 15m, 1h, and 24h
    for lag in [1, 4, 96,672, 2880]:
        data[f'{target_sensor}_lag_{lag}'] = data[target_sensor].shift(lag)

    # 3. Spatial Lag features for NEIGHBORS (Sensors 1, 2, 3)
    # These provide "upstream" context
    neighbors = [c for c in final_df.columns if c != target_sensor]

    for s in neighbors:
            data[f'{s}_lag_1'] = data[s].shift(1)  # What happened 15 mins ago upstream?
            data[f'{s}_lag_4'] = data[s].shift(4)  # What happened 1 hour ago upstream?
            data[f'{s}_lag_672']  = data[s].shift(672)   # 1 week ago upstream
            data[f'{s}_lag_2880'] = data[s].shift(2880)
            data[f'{s}_roc_1']  = data[s].diff(1)   # upstream rate of change
            data[f'{s}_roc_4']  = data[s].diff(4)   # upstream hourly change
            data[f'{s}_roc_672']  = data[s].diff(672)   # upstream weekly change
            data[f'{s}_roc_2880'] = data[s].diff(2880)  # upstream monthly change

    # 4. Rolling statistics (Trend)
    data['rolling_mean_6h'] = data[target_sensor].shift(1).rolling(window=24).mean()

    # In Cell 9, after rolling_mean_6h:

    # Rate of change (is the signal rising or falling fast?)
    data['roc_1']  = data[target_sensor].diff(1)   # 15-min change
    data['roc_4']  = data[target_sensor].diff(4)   # 1-hour change
    data['roc_96'] = data[target_sensor].diff(96)  # 24-hour change

    # Volatility (is the signal stable or jumping around?)
    data['rolling_std_6h']  = data[target_sensor].shift(1).rolling(window=24).std()
    data['rolling_std_24h'] = data[target_sensor].shift(1).rolling(window=96).std()

    # Rolling min/max (captures the range of recent behaviour)
    data['rolling_max_24h'] = data[target_sensor].shift(1).rolling(window=96).max()
    data['rolling_min_24h'] = data[target_sensor].shift(1).rolling(window=96).min()


    data.dropna(inplace=True)
    df_featured = data.copy()
    print(f"df_featured shape: {df_featured.shape}")
    print(f"Date range: {df_featured.index.min()} → {df_featured.index.max()}")
    return df_featured

def datapreparation(df_featured):
    # Split based on your specific dates
    train_data = df_featured[:'2025-06-30'] # all data up to June 2025
    test_data = df_featured['2025-07-01':'2025-07-30'] # ground truth month

    X_train = train_data.drop(columns=sensors)  # Drop original sensor columns
    y_train = train_data[target_sensor]

    X_test = test_data.drop(columns=sensors)
    y_test = test_data[target_sensor]

    # Does the data contain high conductivity events? 
    print("Train conductivity range:", y_train.min(), "→", y_train.max())
    print("Test  conductivity range:", y_test.min(),  "→", y_test.max())
    return X_train, y_train, X_test, y_test
#####################################################################################################
def lightGBM_train(X_train, y_train, X_test, y_test):
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

def lightGBM_forecast_bias(model, X_test, y_test):
    forecast = model.predict(X_test)
    mae = mean_absolute_error(y_test, forecast)
    print(f"September 2025 Forecast MAE: {mae:.4f} units of conductivity")
    error = y_test - forecast
    print(f"Mean Error (Bias): {error.mean()}")
    return forecast, mae, error

def lightGBM_visualization(y_test, forecast):
    # 1. Create a DataFrame for easy plotting
    results = pd.DataFrame({
        'Actual': y_test,
        'Forecast': forecast
    }, index=y_test.index)

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
    plt.show(block=False)
    plt.pause(0.1) # Gives the GUI time to render
#####################################################################################################
def xgboost_train(X_train, y_train, X_test, y_test):
    dtrain = xgb.DMatrix(X_train, label=y_train)
    dtest = xgb.DMatrix(X_test, label=y_test)
    params = {
        'objective': 'reg:squarederror', # We are predicting a number (conductivity)
        'max_depth': 6,                 # Depth of trees
        'eta': 0.01,                    # Learning rate (same as 'learning_rate')
        'subsample': 0.8,               # Use 80% of data to grow each tree (prevents overfitting)
        'colsample_bytree': 0.8,        # Use 80% of sensors for each tree
        'eval_metric': 'mae'
    }
    # We use 'evallist' to watch the error in real-time
    evallist = [(dtrain, 'train'), (dtest, 'eval')]
    num_round = 2000
    bst = xgb.train(params, dtrain, num_round, evallist, early_stopping_rounds=50)
    # 4. Forecast 
    predictions_xgb = bst.predict(dtest)
    return predictions_xgb

def xgboost_forecast_bias(predictions_xgb, y_test):
    mae_xgb = mean_absolute_error(y_test, predictions_xgb)
    print(f"XGBoost  MAE: {mae_xgb:.4f}")
    return mae_xgb

def xgboost_visualization(predictions_xgb, y_test):
    # 1. Create a DataFrame for XGBoost results
    # Ensure 'predictions_xgb' is the output from bst.predict(dtest)
    results_xgb = pd.DataFrame({
        'Actual': y_test,
        'XGBoost_Forecast': predictions_xgb
    }, index=y_test.index)

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
    plt.show()
#####################################################################################################
def comparisonforecast(forecast, predictions_xgb, y_test):
    # Head to head comparison
    comparison = pd.DataFrame({
        'Actual':   y_test.values[:2688],
        'LightGBM': forecast[:2688],
        'XGBoost':  predictions_xgb[:2688]
    }, index=y_test.index[:2688]) 
    return comparison

def comparison_visualization(comparison): 
    plt.figure(figsize=(15, 8))
    plt.plot(comparison['Actual'],   label='Actual',    color='black', alpha=0.4, linewidth=2)
    plt.plot(comparison['LightGBM'], label='LightGBM',  color='red',   linestyle=':',  alpha=0.8)
    plt.plot(comparison['XGBoost'],  label='XGBoost',   color='green', linestyle='--', alpha=0.8)

    plt.title('Comparison: LightGBM vs XGBoost vs Ground Truth')
    plt.xlabel('Date')
    plt.ylabel('Conductivity (μS/cm)')
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()      
#####################################################################################################
def main():
    sensor_set = identify_unique_sensors()
    final_df   = reframe_data(sensor_set)
    plot_sensor_data(final_df)
    df_featured = featureengineering(final_df)
    X_train, y_train, X_test, y_test = datapreparation(df_featured)

    model = lightGBM_train(X_train, y_train, X_test, y_test)
    forecast, mae, error = lightGBM_forecast_bias(model, X_test, y_test)
    lightGBM_visualization(y_test, forecast)

    predictions_xgb = xgboost_train(X_train, y_train, X_test, y_test)
    mae_xgb = xgboost_forecast_bias(predictions_xgb, y_test)
    xgboost_visualization(predictions_xgb, y_test)

    comparison = comparisonforecast(forecast, predictions_xgb, y_test)
    comparison_visualization(comparison)

if __name__ == "__main__":
    main()