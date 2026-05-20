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


async def reframe_data(sensor_set):
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

    final_df = final_df.sort_values('time').set_index('time')
    print("Finished!")
    print(final_df.head())
    return final_df

async def featureengineering(final_df):
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
    df_featured = data.copy()
    print(f"df_featured shape: {df_featured.shape}")
    print(f"Date range: {df_featured.index.min()} → {df_featured.index.max()}")
    return df_featured

async def datapreparation(df_featured):
    # Split based on your specific dates
    train_data = df_featured[:'2025-06-30'] # all data up to June 2025
    test_data = df_featured['2025-07-01':'2025-07-30'] # ground truth month

    X_train = train_data.drop(columns=constants.sensors)  # Drop original sensor columns
    y_train = train_data[constants.target_sensor]

    X_test = test_data.drop(columns=constants.sensors)
    y_test = test_data[constants.target_sensor]

    # Does the data contain high conductivity events? 
    print("Train conductivity range:", y_train.min(), "→", y_train.max())
    print("Test  conductivity range:", y_test.min(),  "→", y_test.max())
    return X_train, y_train, X_test, y_test
#####################################################################################################