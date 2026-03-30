import os
import pickle
import numpy as np
import pandas as pd
import requests
import tensorflow as tf
from tensorflow.keras import layers, regularizers, Model
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error

# --- Configuration ---
VIRTUOSO_URL = "http://localhost:8890/sparql"
GRAPH_URI    = "http://example.com/Gent-Terneuzen"
USERNAME     = "dba"
PASSWORD     = "dba"
AUTH         = (USERNAME, PASSWORD)

def main():
    # ---------------------------------------------------------
    # 1. Identify unique sensors
    # ---------------------------------------------------------
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
        print(f"Error fetching sensors: {res.status_code}")
        return
    else:
        print("Unique sensors identified successfully!")

    bindings = res.json()['results']['bindings']
    for row in bindings:
        sensor_set.add(row['sensor']['value'])

    print(f"Added {len(sensor_set)} unique sensors: {sensor_set}")

    # ---------------------------------------------------------
    # 2. Reframe the data
    # ---------------------------------------------------------
    final_df = pd.DataFrame()
    print("\nFetching and pivoting sensor data...")

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

    if final_df.empty:
        print("No data fetched. Exiting.")
        return

    final_df = final_df.sort_values('time').set_index('time')
    print("Data fetching finished!")

    # ---------------------------------------------------------
    # 3. Pre-processing
    # ---------------------------------------------------------
    df_clean = final_df.copy()
    df_clean = df_clean.ffill().bfill()

    feature_sensors = ['289435042', '289423042', '289429042', '289441042']
    target_sensor   = '289441042'
    
    # Ensure all required sensors are in the dataframe
    missing_sensors = [s for s in feature_sensors if s not in df_clean.columns]
    if missing_sensors:
        print(f"Missing required sensors in data: {missing_sensors}. Exiting.")
        return

    target_col_idx  = feature_sensors.index(target_sensor)
    n_features      = len(feature_sensors)

    data_arr = df_clean[feature_sensors].values

    # Split and scale
    split_index  = int(len(data_arr) * 0.8)
    train_data   = data_arr[:split_index]
    test_data    = data_arr[split_index:]

    scaler        = MinMaxScaler(feature_range=(0, 1))
    train_scaled  = scaler.fit_transform(train_data)
    test_scaled   = scaler.transform(test_data)

    print(f"\nTrain samples: {len(train_scaled):,}  |  Test samples: {len(test_scaled):,}")

    # ---------------------------------------------------------
    # 4. Sliding-window sequences
    # ---------------------------------------------------------
    time_steps = 672   # 1 week of 15-min readings
    n_future   = 96    # 24 hours ahead

    def create_sequences(dataset, time_steps, n_future, target_col):
        X, y = [], []
        for i in range(len(dataset) - time_steps - n_future + 1):
            X.append(dataset[i : i + time_steps, :])
            y.append(dataset[i + time_steps : i + time_steps + n_future, target_col])
        return np.array(X), np.array(y)

    X_train, y_train = create_sequences(train_scaled, time_steps, n_future, target_col_idx)
    X_test,  y_test  = create_sequences(test_scaled,  time_steps, n_future, target_col_idx)

    print(f"X_train: {X_train.shape}  →  (samples, time_steps, n_features)")
    print(f"y_train: {y_train.shape}  →  (samples, n_future)")

    # ---------------------------------------------------------
    # 5. Stage 1 — LSTM denoising autoencoder (pre-training)
    # ---------------------------------------------------------
    print("\n--- Starting Stage 1: Autoencoder Pre-training ---")
    def build_lstm_autoencoder(time_steps, n_features, bottleneck=32, dropout_rate=0.1, l2_reg=1e-4, noise_std=0.05):
        reg = regularizers.l2(l2_reg)

        # Encoder
        enc_input = layers.Input(shape=(time_steps, n_features), name='enc_input')
        x = layers.GaussianNoise(noise_std)(enc_input)
        x = layers.LSTM(64, return_sequences=True, kernel_regularizer=reg, name='lstm_enc_1')(x)
        x = layers.Dropout(dropout_rate)(x)
        z = layers.LSTM(bottleneck, return_sequences=False, kernel_regularizer=reg, name='bottleneck')(x)

        # Decoder
        x = layers.RepeatVector(time_steps)(z)
        x = layers.LSTM(bottleneck, return_sequences=True, kernel_regularizer=reg, name='lstm_dec_1')(x)
        x = layers.Dropout(dropout_rate)(x)
        x = layers.LSTM(64, return_sequences=True, kernel_regularizer=reg, name='lstm_dec_2')(x)
        dec_output = layers.TimeDistributed(layers.Dense(n_features, activation='sigmoid'), name='reconstruction')(x)

        autoencoder = Model(enc_input, dec_output, name='lstm_autoencoder')
        autoencoder.compile(optimizer=tf.keras.optimizers.Adam(1e-3), loss='mse')
        return autoencoder

    autoencoder = build_lstm_autoencoder(time_steps, n_features, bottleneck=32)

    early_stop_ae = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True, verbose=1)
    reduce_lr_ae = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-6, verbose=1)

    autoencoder.fit(
        X_train, X_train,
        epochs=100,
        batch_size=32,
        validation_split=0.1,
        callbacks=[early_stop_ae, reduce_lr_ae],
        verbose=1
    )

    # ---------------------------------------------------------
    # 6. Stage 2 — Attach forecasting head and fine-tune
    # ---------------------------------------------------------
    print("\n--- Starting Stage 2: Forecaster Training ---")
    encoder = Model(inputs=autoencoder.input, outputs=autoencoder.get_layer('bottleneck').output, name='lstm_encoder')
    
    for layer in encoder.layers:
        layer.trainable = False

    fc_input  = layers.Input(shape=(time_steps, n_features), name='fc_input')
    z         = encoder(fc_input)
    fc_output = layers.Dense(n_future, name='forecast')(z)

    forecaster = Model(fc_input, fc_output, name='forecaster')
    forecaster.compile(optimizer=tf.keras.optimizers.Adam(1e-3), loss='mse')

    print("\nPhase 1: Training forecast head (encoder frozen)...")
    early_stop_p1 = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True, verbose=1)
    reduce_lr_p1  = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-6, verbose=1)

    forecaster.fit(
        X_train, y_train,
        epochs=100,
        batch_size=32,
        validation_split=0.1,
        callbacks=[early_stop_p1, reduce_lr_p1],
        verbose=1
    )

    print("\nPhase 2: End-to-end fine-tuning (unfrozen)...")
    encoder.trainable = True
    forecaster.compile(optimizer=tf.keras.optimizers.Adam(1e-5), loss='mse')

    early_stop_p2 = EarlyStopping(monitor='val_loss', patience=15, restore_best_weights=True, verbose=1)
    reduce_lr_p2  = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=7, min_lr=1e-8, verbose=1)

    forecaster.fit(
        X_train, y_train,
        epochs=100,
        batch_size=32,
        validation_split=0.1,
        callbacks=[early_stop_p2, reduce_lr_p2],
        verbose=1
    )

    # ---------------------------------------------------------
    # 7. Save Model and Scaler
    # ---------------------------------------------------------
    print("\n--- Saving Model and Scaler ---")
    model_path = "lstm_forecaster.keras"
    scaler_path = "scaler.pkl"
    
    forecaster.save(model_path)
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
        
    print(f"Model saved to {model_path}")
    print(f"Scaler saved to {scaler_path}")

    # ---------------------------------------------------------
    # 8. Evaluation
    # ---------------------------------------------------------
    print("\n--- Evaluation on Test Set ---")
    test_preds_scaled = forecaster.predict(X_test)
    
    print(f"\n{'Step':<8} {'MAE':>8} {'RMSE':>8}")
    print("-" * 26)
    
    for step in range(n_future):
        dummy_p = np.zeros((len(test_preds_scaled), n_features))
        dummy_p[:, target_col_idx] = test_preds_scaled[:, step]
        preds_real = scaler.inverse_transform(dummy_p)[:, target_col_idx]

        dummy_t = np.zeros((len(y_test), n_features))
        dummy_t[:, target_col_idx] = y_test[:, step]
        true_real = scaler.inverse_transform(dummy_t)[:, target_col_idx]

        mae  = mean_absolute_error(true_real, preds_real)
        rmse = np.sqrt(mean_squared_error(true_real, preds_real))
        
        if step % 12 == 0:
            print(f"  t+{step+1:<4}  {mae:>7.2f}  {rmse:>7.2f}")

    # Example 24 hour forecast printout
    full_scaled   = np.concatenate([train_scaled, test_scaled], axis=0)
    last_sequence = full_scaled[-time_steps:]              
    last_sequence = np.expand_dims(last_sequence, axis=0)  

    scaled_forecast = forecaster.predict(last_sequence)    

    dummy = np.zeros((n_future, n_features))
    dummy[:, target_col_idx] = scaled_forecast[0]
    forecast_real = scaler.inverse_transform(dummy)[:, target_col_idx]

    print(f"\nForecast for the next {n_future} steps (sensor {target_sensor}):")
    for i, val in enumerate(forecast_real, 1):
        if i % 12 == 0 or i == 1:
            print(f"  t+{i:3d}: {val:.2f}")

if __name__ == "__main__":
    main()