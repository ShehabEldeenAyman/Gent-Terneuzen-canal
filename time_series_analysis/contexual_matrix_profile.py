import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

import numpy as np
from distancematrix.generator.euclidean import Euclidean
from distancematrix.consumer.radius_profile import RadiusProfile
from distancematrix.consumer.matrix_profile_lr import MatrixProfileLR
from distancematrix.generator.znorm_euclidean import ZNormEuclidean
from distancematrix.consumer.multidimensional_matrix_profile_lr import MultidimensionalMatrixProfileLR
from distancematrix.consumer.matrix_profile_lr import MatrixProfileLR
from distancematrix.calculator import AnytimeCalculator


VIRTUOSO_URL = "http://localhost:8890/sparql"
GRAPH_URI    = "http://example.com/Gent-Terneuzen"
USERNAME     = "dba"
PASSWORD     = "dba"
AUTH         = (USERNAME, PASSWORD)
params  = {'graph': GRAPH_URI}
headers = {'Accept': 'text/turtle'}

sensors = ['289435042', '289423042', '289429042', '289441042']
colors  = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']

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

