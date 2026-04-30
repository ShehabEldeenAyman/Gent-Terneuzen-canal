import { useEffect, useState } from 'react';
import * as tf from '@tensorflow/tfjs';
import { sensor_data } from './testCard';

export default function TensorflowConductivity() {
  const [modelStatus, setModelStatus] = useState("Waiting for data...");

  const trainModel = async () => {
    const dataMap = sensor_data.sensorDataMap;
    const sensorIds = Object.keys(dataMap);

    if (sensorIds.length === 0) {
      setModelStatus("No data found. Load data in TestCard first.");
      return;
    }

    setModelStatus("Processing data...");

    // 1. Prepare Data: Combine all sensor values into one sequence
    // We only care about the values [1] for prediction, not the timestamps [0]
    let allValues = [];
    sensorIds.forEach(id => {
      const values = dataMap[id].map(point => point[1]);
      allValues = allValues.concat(values);
    });

    // 2. Create Windows (Sliding Window of size 10)
    const windowSize = 10;
    const inputs = [];
    const labels = [];

    for (let i = 0; i < allValues.length - windowSize; i++) {
      const window = allValues.slice(i, i + windowSize);
      inputs.push(window);
      labels.push(allValues[i + windowSize]);
    }

    // 3. Convert to Tensors
    // Shape: [batch_size, window_size, features] -> [N, 10, 1]
    const xs = tf.tensor2d(inputs).reshape([inputs.length, windowSize, 1]);
    const ys = tf.tensor2d(labels, [labels.length, 1]);

    // 4. Define the Model (LSTM)
    const model = tf.sequential();
    model.add(tf.layers.lstm({
      units: 20,
      inputShape: [windowSize, 1],
      returnSequences: false
    }));
    model.add(tf.layers.dense({ units: 1 }));

    model.compile({
      optimizer: tf.train.adam(),
      loss: 'meanSquaredError'
    });

    // 5. Train
    setModelStatus("Training...");
    await model.fit(xs, ys, {
      epochs: 20,
      callbacks: {
        onEpochEnd: (epoch, logs) => {
          console.log(`Epoch ${epoch}: loss = ${logs.loss}`);
        }
      }
    });

    setModelStatus("Training Complete! Ready for prediction.");
    
    // Save model to memory or local storage if needed
    // await model.save('localstorage://my-model');
  };

  return (
    <div style={{ padding: '20px' }}>
      <h3>TensorFlow Prediction</h3>
      <p>Status: <strong>{modelStatus}</strong></p>
      <button onClick={trainModel} style={{ padding: '10px' }}>
        Train Model on Sensor Data
      </button>
    </div>
  );
}