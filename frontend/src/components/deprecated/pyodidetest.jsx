// src/App.jsx
import { useState, useEffect, useRef } from 'react';
// Vite syntax to import a web worker
import PythonWorker from './python.worker.js?worker';

export function pyodidetest() {
  const [output, setOutput] = useState('');
  const [figure, setFigure] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const workerRef = useRef(null);

  useEffect(() => {
    // Initialize the worker
    workerRef.current = new PythonWorker();

    // Listen for results from the worker
    workerRef.current.onmessage = (event) => {
      const { success, results, image, error } = event.data;
      setIsRunning(false);
      
      if (success) {
        setOutput(results);
        if (image) {
          setFigure(`data:image/png;base64,${image}`);
        }
      } else {
        setOutput(`Error: ${error}`);
      }
    };

    // Cleanup worker on unmount
    return () => {
      if (workerRef.current) workerRef.current.terminate();
    };
  }, []);

  const runChronosPipeline = () => {
    if (!workerRef.current) return;
    setIsRunning(true);
    setOutput('Loading Pyodide environment and running pipeline...');
    setFigure(null);

    // Python script containing data generation, forecasting framework, and Base64 image exporting
    const pythonCode = `
import io
import base64
import numpy as np
import pandas as pd

# Switch matplotlib backend to non-interactive Agg before importing pyplot
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# --- Chronos-2 Pipeline Mock for Pyodide/Browser compatibility ---
class Chronos2Pipeline:
    @classmethod
    def from_pretrained(cls, model_name, device_map="cpu"):
        return cls()

    def predict_df(self, df, prediction_length, id_column, timestamp_column, target, quantile_levels):
        last_date = df[timestamp_column].max()
        forecast_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=prediction_length, freq="D")
        
        # Simulate a realistic continuity of trend + weekly seasonality + confidence intervals
        x_future = np.arange(100, 100 + prediction_length)
        base_trend = np.linspace(50, 55, prediction_length)
        seasonal_wave = 15 * np.sin(x_future * (2 * np.pi / 7))
        median_forecast = base_trend + seasonal_wave

        return pd.DataFrame({
            timestamp_column: forecast_dates,
            "0.1": median_forecast - 6.5,
            "0.5": median_forecast,
            "0.9": median_forecast + 6.5
        })

# 1. Create a dummy time series with a weekly pattern
np.random.seed(42)
dates = pd.date_range(start="2026-01-01", periods=100, freq="D")
values = np.linspace(10, 50, 100) + 15 * np.sin(np.arange(100) * (2 * np.pi / 7)) + np.random.normal(0, 2, 100)

df = pd.DataFrame({
    "item_id": ["sensor_1"] * 100,
    "timestamp": dates,
    "target": values
})

# 2. Load the Chronos-2 Model 
pipeline = Chronos2Pipeline.from_pretrained("amazon/chronos-2", device_map="cpu")

# 3. Generate Forecasts
prediction_length = 14
forecast_df = pipeline.predict_df(
    df=df,
    prediction_length=prediction_length,
    id_column="item_id",
    timestamp_column="timestamp",
    target="target",
    quantile_levels=[0.1, 0.5, 0.9]
)

# Capture DataFrame head log output
output_log = str(forecast_df.head())

# 4. Plotting the results
plt.figure(figsize=(10, 5))
plt.plot(df["timestamp"], df["target"], label="Historical Data", color="black")
plt.plot(forecast_df["timestamp"], forecast_df["0.5"], label="Chronos-2 Forecast (Median)", color="blue", linestyle="--")
plt.fill_between(
    forecast_df["timestamp"], 
    forecast_df["0.1"], 
    forecast_df["0.9"], 
    alpha=0.2, 
    color="blue", 
    label="80% Prediction Interval"
)
plt.title("Chronos-2 Zero-Shot Forecast Demo")
plt.xlabel("Date")
plt.ylabel("Value")
plt.legend()
plt.grid(True, linestyle=":")

# Save figure directly to a string buffer to extract via JavaScript
buf = io.BytesIO()
plt.savefig(buf, format='png', bbox_inches='tight')
buf.seek(0)
img_base64 = base64.b64encode(buf.read()).decode('utf-8')
plt.close()
`;

    workerRef.current.postMessage({ code: pythonCode });
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif', maxWidth: '900px', margin: '0 auto' }}>
      <h2>In-Browser Time Series Forecaster</h2>
      <p style={{ color: '#666' }}>Runs pipeline data structures natively via Pyodide WebAssembly.</p>
      
      <button 
        onClick={runChronosPipeline} 
        disabled={isRunning} 
        style={{ 
          padding: '12px 24px', 
          fontSize: '16px', 
          backgroundColor: isRunning ? '#ccc' : '#0070f3', 
          color: '#fff', 
          border: 'none', 
          borderRadius: '5px', 
          cursor: isRunning ? 'not-allowed' : 'pointer' 
        }}
      >
        {isRunning ? 'Executing Forecast Model...' : 'Run Chronos Pipeline'}
      </button>

      <h3 style={{ marginTop: '25px' }}>Console Output:</h3>
      <pre style={{ backgroundColor: '#f4f4f4', padding: '15px', borderRadius: '5px', fontFamily: 'monospace', overflowX: 'auto' }}>
        {output}
      </pre>

      {figure && (
        <div style={{ marginTop: '25px' }}>
          <h3>Generated Figure:</h3>
          <div style={{ backgroundColor: '#fff', border: '1px solid #ddd', borderRadius: '5px', padding: '10px' }}>
            <img src={figure} alt="Chronos-2 Forecast Plot" style={{ width: '100%', height: 'auto' }} />
          </div>
        </div>
      )}
    </div>
  );
}