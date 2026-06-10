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
#import lightgbm as lgb
#import xgboost as xgb

import constants


async def identify_unique_sensors():
    sensor_set = set()

    sensor_query = f"""
        PREFIX sosa: <http://www.w3.org/ns/sosa/>
        SELECT DISTINCT ?sensor
        WHERE {{
            GRAPH <{constants.GRAPH_URI}> {{
                ?obs a sosa:Observation ;
                    sosa:madeBySensor ?sensor .
            }}
        }}
        """
    res = requests.get(constants.VIRTUOSO_URL, params={'query': sensor_query, 'format': 'application/sparql-results+json'})
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


async def reframe_data(sensor_set, after=None, before=None):
    final_df = pd.DataFrame()
    print("Fetching and pivoting sensor data...")

    for sensor_uri in sensor_set:
        column_name = sensor_uri.split('/')[-1]
        query = f"""
            PREFIX sosa: <http://www.w3.org/ns/sosa/>
            PREFIX ex: <http://example.com/attributes/>
            SELECT ?time ?value ?unixtime
            WHERE {{
                GRAPH <{constants.GRAPH_URI}> {{
                    ?obs a sosa:Observation ;
                        sosa:resultTime ?time ;
                        sosa:hasSimpleResult ?value ;
                        ex:unixTimestamp ?unixtime ;
                        sosa:madeBySensor <{sensor_uri}> .
                }}
            }}
        """
        res = requests.get(constants.VIRTUOSO_URL, params={'query': query, 'format': 'application/sparql-results+json'})
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

    print("All sensors fetched and pivoted successfully!")
    print(f"Final DataFrame shape: {final_df.shape}")
    print(final_df.head())

    final_df = final_df.sort_values('time').set_index('time')

    if after is not None:
        final_df = final_df[final_df.index >= pd.Timestamp(after, tz='UTC')]
    if before is not None:
        final_df = final_df[final_df.index <= pd.Timestamp(before, tz='UTC')]

    print("Finished!")
    print(final_df.head())
    return final_df

async def featureengineering(final_df, fit=True):
    data = final_df.copy()

    # 1. Time-based features (Seasonality)
    data['hour'] = data.index.hour
    data['day_of_week'] = data.index.dayofweek
    data['month'] = data.index.month

    # 2. Lag features for the TARGET (Sensor 4)
    for lag in [1, 4, 96, 672, 2880]:
        data[f'{constants.target_sensor}_lag_{lag}'] = data[constants.target_sensor].shift(lag)

    # 3. Spatial Lag features for NEIGHBORS (Sensors 1, 2, 3)
    neighbors = [c for c in final_df.columns if c != constants.target_sensor]

    for s in neighbors:
        data[f'{s}_lag_1']    = data[s].shift(1)
        data[f'{s}_lag_4']    = data[s].shift(4)
        data[f'{s}_lag_672']  = data[s].shift(672)
        data[f'{s}_lag_2880'] = data[s].shift(2880)
        data[f'{s}_roc_1']    = data[s].shift(1).diff(1)    # FIXED: was data[s].diff(1)
        data[f'{s}_roc_4']    = data[s].shift(1).diff(4)    # FIXED: was data[s].diff(4)
        data[f'{s}_roc_672']  = data[s].shift(1).diff(672)  # FIXED: was data[s].diff(672)
        data[f'{s}_roc_2880'] = data[s].shift(1).diff(2880) # FIXED: was data[s].diff(2880)

    # 4. Rolling statistics (Trend) — already correctly shifted
    data['rolling_mean_6h'] = data[constants.target_sensor].shift(1).rolling(window=24).mean()

    # 5. Rate of change for TARGET — FIXED: added .shift(1) before .diff()
    data['roc_1']  = data[constants.target_sensor].shift(1).diff(1)   # FIXED
    data['roc_4']  = data[constants.target_sensor].shift(1).diff(4)   # FIXED
    data['roc_96'] = data[constants.target_sensor].shift(1).diff(96)  # FIXED

    # 6. Volatility — already correctly shifted
    data['rolling_std_6h']  = data[constants.target_sensor].shift(1).rolling(window=24).std()
    data['rolling_std_24h'] = data[constants.target_sensor].shift(1).rolling(window=96).std()

    # 7. Rolling min/max — already correctly shifted
    data['rolling_max_24h'] = data[constants.target_sensor].shift(1).rolling(window=96).max()
    data['rolling_min_24h'] = data[constants.target_sensor].shift(1).rolling(window=96).min()

    data.dropna(inplace=True)
    print(f"Feature shape: {data.shape}, Date range: {data.index.min()} → {data.index.max()}")
    X = data.drop(columns=constants.sensors)
    y = data[constants.target_sensor]
    return X, y
    data = final_df.copy()
    

    # 1. Time-based features (Seasonality)
    data['hour'] = data.index.hour
    data['day_of_week'] = data.index.dayofweek
    data['month'] = data.index.month


    # 2. Lag features for the TARGET (Sensor 4)
        # We look back 15m, 1h, and 24h
    for lag in [1, 4, 96,672, 2880]:
        data[f'{constants.target_sensor}_lag_{lag}'] = data[constants.target_sensor].shift(lag)

    # 3. Spatial Lag features for NEIGHBORS (Sensors 1, 2, 3)
    # These provide "upstream" context
    neighbors = [c for c in final_df.columns if c != constants.target_sensor]

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
    data['rolling_mean_6h'] = data[constants.target_sensor].shift(1).rolling(window=24).mean()

    # In Cell 9, after rolling_mean_6h:

    # Rate of change (is the signal rising or falling fast?)
    data['roc_1']  = data[constants.target_sensor].diff(1)   # 15-min change
    data['roc_4']  = data[constants.target_sensor].diff(4)   # 1-hour change
    data['roc_96'] = data[constants.target_sensor].diff(96)  # 24-hour change

    # Volatility (is the signal stable or jumping around?)
    data['rolling_std_6h']  = data[constants.target_sensor].shift(1).rolling(window=24).std()
    data['rolling_std_24h'] = data[constants.target_sensor].shift(1).rolling(window=96).std()

    # Rolling min/max (captures the range of recent behaviour)
    data['rolling_max_24h'] = data[constants.target_sensor].shift(1).rolling(window=96).max()
    data['rolling_min_24h'] = data[constants.target_sensor].shift(1).rolling(window=96).min()


    data.dropna(inplace=True)
    print(f"Feature shape: {data.shape}, Date range: {data.index.min()} → {data.index.max()}")
    X = data.drop(columns=constants.sensors)        # <-- drop sensors here, not in datapreparation
    y = data[constants.target_sensor]
    return X, y       

async def datapreparation(final_df):
    # 1. Enforce strict 15-min frequency and interpolate gaps
    # This ensures dropna() won't wipe out your test set due to missing sensor readings!
    df = final_df.resample('15min').interpolate(method='time')
    df = df.bfill().ffill()

    # 2. Perform the split
    train_df = df[:'2025-12-27']
    test_df  = df['2025-12-28':'2025-12-31']
    
    print("Train conductivity range:", train_df[constants.target_sensor].min(), "→", train_df[constants.target_sensor].max())
    print("Test  conductivity range:", test_df[constants.target_sensor].min(),  "→", test_df[constants.target_sensor].max())
    
    return train_df, test_df
#####################################################################################################
async def prepare_for_chronos(final_df, target_sensor=None):
    df = final_df.copy()
    df = df['2021-01-01':'2026-02-28']
    # 1. Drop unixtime — Chronos doesn't need it
    df = df.drop(columns=['unixtime'], errors='ignore')
    
    # 2. Enforce strict frequency and handle missing data across all individual sensors
    # Using 'time' interpolation followed by both bfill() and ffill() guarantees 
    # absolutely zero NaN values remaining in the dataset.
    df = df.resample('15min').interpolate(method='time')
    df = df.bfill().ffill()

    # 3. Calculate the row-wise average of all sensors
    # Since 'time' is currently the index, all columns in 'df' right now are your sensors.
    # axis=1 calculates the mean horizontally across columns for each timestamp.
    df['target'] = df.mean(axis=1)
    
    # 4. Isolate just the new average column
    df = df[['target']]

    # 5. Reset index so 'time' becomes a regular column named 'timestamp'
    df = df.reset_index().rename(columns={'time': 'timestamp'})
    
    # 6. Format for Chronos requirement
    # Even for a single averaged series, Chronos still requires an 'item_id' identifier column.
    df.insert(0, 'item_id', 'average_sensor')
    
    # 7. Final cleaning: Ensure datetime formatting and explicit chronological ordering
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    chronos_df = df.sort_values(by=['timestamp']).reset_index(drop=True)
    
    return chronos_df

async def prepare_for_chronos_no_avg(final_df):
    df = final_df.copy()
    df = df['2021-01-01':'2026-02-28']

    # 1. Drop unixtime
    df = df.drop(columns=['unixtime'], errors='ignore')

    # 2. Enforce strict 15-min frequency and fill gaps
    df = df.resample('15min').interpolate(method='time')
    df = df.bfill().ffill()

    # 3. Reset index so 'time' becomes a regular column
    df = df.reset_index().rename(columns={'time': 'timestamp'})

    # 4. Melt from wide to long — each sensor becomes its own item_id
    chronos_df = df.melt(
        id_vars='timestamp',
        var_name='item_id',
        value_name='target'
    )

    # 5. Final sort: group by item, then chronological within each group
    chronos_df = chronos_df.sort_values(
        by=['item_id', 'timestamp']
    ).reset_index(drop=True)

    return chronos_df