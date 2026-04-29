import { useState, useEffect } from 'react';
import * as tf from '@tensorflow/tfjs';

export default function CustomTensorflowBrowser() {
  const [status, setStatus] = useState('Initializing...');
  const [prediction, setPrediction] = useState(null);
  const [model, setModel] = useState(null);

  useEffect(() => {
    const setupModel = async () => {
      // 1. Wait for TFJS to be ready (it will auto-detect WebGL or CPU)
      await tf.ready();
      console.log("Using backend:", tf.getBackend());

      // 2. Define a simple sequential model
      const customModel = tf.sequential();
      
      // Add a single dense layer (1 input, 1 output)
      customModel.add(tf.layers.dense({ units: 1, inputShape: [1] }));

      // 3. Prepare for training
      customModel.compile({
        loss: 'meanSquaredError',
        optimizer: 'sgd', 
      });

      // 4. Generate data: y = 2x - 1
      const xs = tf.tensor2d([-1, 0, 1, 2, 3, 4], [6, 1]);
      const ys = tf.tensor2d([-3, -1, 1, 3, 5, 7], [6, 1]);

      // 5. Train the model
      setStatus('Training model...');
      await customModel.fit(xs, ys, {
        epochs: 250,
        callbacks: {
          onEpochEnd: (epoch, logs) => {
            if (epoch % 50 === 0) console.log(`Epoch ${epoch}: loss = ${logs.loss}`);
          }
        }
      });

      setModel(customModel);
      setStatus('Model Ready');

      // Manual cleanup for training tensors
      xs.dispose();
      ys.dispose();
    };

    setupModel();
  }, []);

  const handlePredict = () => {
    if (!model) return;

    tf.tidy(() => {
      const inputVal = 10;
      const inputTensor = tf.tensor2d([inputVal], [1, 1]);
      const outputTensor = model.predict(inputTensor);
      
      const result = outputTensor.dataSync()[0];
      setPrediction({ input: inputVal, output: result.toFixed(2) });
    });
  };

  return (
    <div style={{ textAlign: 'center', padding: '20px', fontFamily: 'sans-serif' }}>
      <h2>Custom Linear Regression</h2>
      <p>Status: <strong>{status}</strong></p>
      
      <button 
        disabled={!model} 
        onClick={handlePredict} 
        style={{ padding: '10px 20px', cursor: model ? 'pointer' : 'not-allowed' }}
      >
        Predict X = 10
      </button>

      {prediction && (
        <div style={{ marginTop: '20px' }}>
          <p>Result: <strong>{prediction.output}</strong></p>
          <small>(Expected ~19.00)</small>
        </div>
      )}
    </div>
  );
}