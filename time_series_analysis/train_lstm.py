# =============================================================================
# Average Conductivity — LSTM Autoencoder Forecaster
# =============================================================================

import numpy as np
import pandas as pd
import requests
import tensorflow as tf
from tensorflow.keras import layers, regularizers, Model
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error

# =============================================================================
# CONFIG
# =============================================================================

VIRTUOSO_URL = "http://localhost:8890/sparql"
GRAPH_URI    = "http://example.com/Gent-Terneuzen"
USERNAME     = "dba"
PASSWORD     = "dba"
MODEL_PATH   = "forecaster.h5"

SENSORS      = ['289435042', '289423042', '289429042', '289441042']
TIME_STEPS   = 672   # 1 week of 15-min readings
N_FUTURE     = 96    # 24 hours ahead
STRIDE       = 24    # 6-hour step — enough samples, low overlap
BATCH_SIZE   = 32

# =============================================================================
# 1. FETCH DATA FROM VIRTUOSO
# =============================================================================

print("Identifying unique sensors...")
sensor_set   = set()
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
    raise RuntimeError(f"Sensor query failed: {res.status_code}\n{res.text}")

for row in res.json()['results']['bindings']:
    sensor_set.add(row['sensor']['value'])
print(f"Found {len(sensor_set)} sensors.")

print("Fetching sensor observations...")
final_df = pd.DataFrame()

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
    if res.status_code != 200:
        print(f"  WARNING: skipping {column_name}, status {res.status_code}")
        continue

    bindings = res.json()['results']['bindings']
    temp_data = [
        {'time': row['time']['value'], column_name: float(row['value']['value']),
         'unixtime': int(row['unixtime']['value'])}
        for row in bindings
    ]
    temp_df = pd.DataFrame(temp_data)
    if temp_df.empty:
        continue

    temp_df['time'] = pd.to_datetime(temp_df['time'])
    if final_df.empty:
        final_df = temp_df
    else:
        final_df = pd.merge(final_df, temp_df, on=['time', 'unixtime'], how='outer')
    print(f"  Added sensor: {column_name}")

final_df = final_df.sort_values('time').set_index('time')

# Keep data up to and including December 2024
final_df = final_df[final_df.index < '2025-01-01']

print(f"Dataset shape: {final_df.shape}  ({final_df.index.min()} → {final_df.index.max()})")

# =============================================================================
# 2. PREPROCESSING
# =============================================================================

df_clean = final_df.copy()
df_clean = df_clean.ffill().bfill()

# Average across sensors — reduces per-sensor noise, single clean signal
df_clean['average_conductivity'] = df_clean[SENSORS].mean(axis=1)

series = df_clean['average_conductivity'].values.reshape(-1, 1)

split_index  = int(len(series) * 0.8)
train_data   = series[:split_index]
test_data    = series[split_index:]

scaler       = MinMaxScaler(feature_range=(0, 1))
train_scaled = scaler.fit_transform(train_data)
test_scaled  = scaler.transform(test_data)

print(f"Train rows: {len(train_scaled):,}  |  Test rows: {len(test_scaled):,}")

# =============================================================================
# 3. SEQUENCE CREATION
# =============================================================================

def create_sequences(dataset, time_steps, n_future, stride):
    """
    dataset : (n_samples, 1) scaled array
    Returns
      X : (samples, time_steps, 1)  — 3-D input for LSTM
      y : (samples, n_future)       — forecast horizon
    """
    X, y = [], []
    for i in range(0, len(dataset) - time_steps - n_future + 1, stride):
        X.append(dataset[i : i + time_steps, :])
        y.append(dataset[i + time_steps : i + time_steps + n_future, 0])
    return np.array(X), np.array(y)


X_train, y_train = create_sequences(train_scaled, TIME_STEPS, N_FUTURE, STRIDE)
X_test,  y_test  = create_sequences(test_scaled,  TIME_STEPS, N_FUTURE, STRIDE)

print(f"X_train: {X_train.shape}  |  y_train: {y_train.shape}")
print(f"X_test:  {X_test.shape}   |  y_test:  {y_test.shape}")

# =============================================================================
# 4. MODEL
# =============================================================================

def build_lstm_autoencoder(time_steps, n_features=1):
    inputs = layers.Input(shape=(time_steps, n_features), name='encoder_input')

    # Encoder
    x          = layers.LSTM(64, return_sequences=True)(inputs)
    x          = layers.Dropout(0.1)(x)
    x          = layers.LSTM(32, return_sequences=False)(x)
    bottleneck = layers.Dense(16, name='bottleneck')(x)

    # Decoder
    x       = layers.RepeatVector(time_steps)(bottleneck)
    x       = layers.LSTM(32, return_sequences=True)(x)
    x       = layers.Dropout(0.1)(x)
    x       = layers.LSTM(64, return_sequences=True)(x)
    outputs = layers.TimeDistributed(layers.Dense(n_features), name='reconstruction')(x)

    autoencoder = Model(inputs, outputs, name='lstm_autoencoder')
    autoencoder.compile(optimizer=tf.keras.optimizers.Adam(1e-3), loss='mse')
    return autoencoder


# =============================================================================
# 5. TRAINING
# =============================================================================

autoencoder = build_lstm_autoencoder(time_steps=TIME_STEPS, n_features=1)
autoencoder.summary()

# Stage 1 — pre-train encoder/decoder on reconstruction
print("\n── Stage 1: Autoencoder pre-training ────────────────────────────────────")
autoencoder.fit(
    X_train, X_train,
    epochs=30,
    batch_size=BATCH_SIZE,
    validation_split=0.1,
    verbose=1
)

# Stage 2 — freeze encoder, train forecast head only
print("\n── Stage 2: Forecast head training (encoder frozen) ─────────────────────")
encoder = Model(
    inputs  = autoencoder.input,
    outputs = autoencoder.get_layer('bottleneck').output,
    name    = 'encoder'
)
for layer in encoder.layers:
    layer.trainable = False

forecast_input  = layers.Input(shape=(TIME_STEPS, 1), name='forecast_input')
z               = encoder(forecast_input)
forecast_output = layers.Dense(N_FUTURE)(z)

forecaster = Model(forecast_input, forecast_output, name='forecaster')
forecaster.compile(optimizer=tf.keras.optimizers.Adam(1e-3), loss='mse')
forecaster.summary()

forecaster.fit(
    X_train, y_train,
    epochs=30,
    batch_size=BATCH_SIZE,
    validation_split=0.1,
    verbose=1
)

# Stage 3 — unfreeze encoder, fine-tune end-to-end
print("\n── Stage 3: End-to-end fine-tuning ──────────────────────────────────────")
for layer in encoder.layers:
    layer.trainable = True

forecaster.compile(optimizer=tf.keras.optimizers.Adam(1e-5), loss='mse')
forecaster.fit(
    X_train, y_train,
    epochs=20,
    batch_size=BATCH_SIZE,
    validation_split=0.1,
    verbose=1
)

# =============================================================================
# 6. EVALUATION
# =============================================================================

print("\n── Per-step evaluation on test set ──────────────────────────────────────")
test_preds_scaled = forecaster.predict(X_test)

print(f"{'Step':<8} {'MAE':>10} {'RMSE':>10}")
print("-" * 30)
for step in range(N_FUTURE):
    preds_real = scaler.inverse_transform(test_preds_scaled[:, step].reshape(-1, 1)).flatten()
    true_real  = scaler.inverse_transform(y_test[:, step].reshape(-1, 1)).flatten()
    mae  = mean_absolute_error(true_real, preds_real)
    rmse = np.sqrt(mean_squared_error(true_real, preds_real))
    print(f"  t+{step+1:<4}  {mae:>10.4f}  {rmse:>10.4f}")

# =============================================================================
# 7. SAVE MODEL
# =============================================================================

forecaster.save(MODEL_PATH)
print(f"\nModel saved to: {MODEL_PATH}")
