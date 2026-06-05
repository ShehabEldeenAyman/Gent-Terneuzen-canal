import React, { useState } from "react";
import * as tf from "@tensorflow/tfjs";
import { DataFactory } from "n3";
import { getLdesState } from "./LDESClientCard";
import ReactECharts from "echarts-for-react";

const { namedNode } = DataFactory;

// ── Constants (must match the notebook) ──────────────────────────────────────
const PREFIXES = {
  TSS: "https://w3id.org/tss#",
  RDF: "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
};

const CONDUCTIVITY_URL = "https://shehabeldeenayman.github.io/Gent-Terneuzen-canal/conductivity/conductivity.trig";
const ldesState = getLdesState(CONDUCTIVITY_URL);

const TARGET_SENSOR_IDS = ["289435042", "289429042", "289441042", "289423042"];
//const TARGET_SENSOR_IDS = ["34967042"];
const TIME_STEPS   = 1344;  // 2 weeks  @ 15-min
const N_FUTURE     = 288;   // 72 hours @ 15-min
const INTERVAL_MS  = 15 * 60 * 1000; // 15 minutes in milliseconds

// Path to your TF.js converted model (see note at bottom of file)
const MODEL_URL = "https://shehabeldeenayman.github.io/Gent-Terneuzen-canal/model.json";


// ── Step 1: Extract sensor data from ldesState ────────────────────────────────
// Mirrors handleLoadData() in datavisualization.jsx exactly.
function extractSensorData() {
  const snippetSubjects = ldesState.store
    .getQuads(null, namedNode(PREFIXES.RDF + "type"), namedNode(PREFIXES.TSS + "Snippet"), null)
    .map(q => q.subject.value);

  const sensorDataMap = {};

  snippetSubjects.forEach(uri => {
    const parts = uri.split("/");
    const waterInfoIndex = parts.indexOf("waterinfo");
    const sensorId = parts[waterInfoIndex + 1];

    if (!TARGET_SENSOR_IDS.includes(sensorId)) return;

    const pointsRecord = ldesState.store.getQuads(
      namedNode(uri),
      namedNode(PREFIXES.TSS + "points"),
      null,
      null
    )[0];

    const rawPoints = pointsRecord?.object.value;
    if (!rawPoints) return;

    const parsedPoints = JSON.parse(rawPoints);
    const formatted = parsedPoints.map(p => [p.time, p.value]);

    if (!sensorDataMap[sensorId]) sensorDataMap[sensorId] = [];
    sensorDataMap[sensorId].push(...formatted);
  });

  // Sort each sensor by time
  Object.keys(sensorDataMap).forEach(id => {
    sensorDataMap[id].sort((a, b) => new Date(a[0]) - new Date(b[0]));
  });

  return sensorDataMap;
}


// ── Step 2: Average sensors → resampled 15-min series ────────────────────────
// Matches: df_clean['average_conductivity'] = df_clean[SENSORS].mean(axis=1)
function buildAverageSeries(sensorDataMap) {
  // Collect all unique timestamps across all sensors (as ms since epoch)
  const allTimestamps = new Set();
  const sensorMaps = {};

  Object.entries(sensorDataMap).forEach(([id, points]) => {
    sensorMaps[id] = {};
    points.forEach(([time, value]) => {
      // Snap to nearest 15-min bucket
      const ms = new Date(time).getTime();
      const bucket = Math.round(ms / INTERVAL_MS) * INTERVAL_MS;
      allTimestamps.add(bucket);
      sensorMaps[id][bucket] = value;
    });
  });

  const sortedTimestamps = Array.from(allTimestamps).sort((a, b) => a - b);
  const sensorIds = Object.keys(sensorMaps);

  // For each 15-min bucket, average the available sensor readings
  const averaged = sortedTimestamps.map(ts => {
    const readings = sensorIds
      .map(id => sensorMaps[id][ts])
      .filter(v => v !== undefined && !isNaN(v));

    const avg = readings.length > 0
      ? readings.reduce((a, b) => a + b, 0) / readings.length
      : null;

    return { ts, value: avg };
  });

  // Forward-fill small gaps (up to 4 steps, matching the notebook's ffill(limit=4))
  for (let i = 1; i < averaged.length; i++) {
    if (averaged[i].value === null) {
      let lookback = 1;
      while (lookback <= 4 && i - lookback >= 0 && averaged[i - lookback].value === null) lookback++;
      if (lookback <= 4 && i - lookback >= 0) {
        averaged[i].value = averaged[i - lookback].value;
      }
    }
  }

  // Drop any still-null entries
  return averaged.filter(d => d.value !== null);
}


// ── Step 3: MinMax scale using scaler params ──────────────────────────────────
// The scaler_v2.pkl params must be exported once from Python and pasted here:
//   import joblib; s = joblib.load("scaler_v2.pkl")
//   print(s.data_min_[0], s.data_max_[0])
//
// Replace the two values below with the actual min/max from your scaler.
const SCALER_MIN = 0.0;    // ← replace with scaler.data_min_[0]
const SCALER_MAX = 1000.0; // ← replace with scaler.data_max_[0]

function minMaxScale(values) {
  return values.map(v => (v - SCALER_MIN) / (SCALER_MAX - SCALER_MIN));
}

function minMaxInverse(scaledValues) {
  return scaledValues.map(v => v * (SCALER_MAX - SCALER_MIN) + SCALER_MIN);
}


// ── Step 4: Prepare model input window ───────────────────────────────────────
// Shape: (1, TIME_STEPS, 1)  →  (1, 1344, 1)
// We leave the last N_FUTURE points as held-out ground truth for comparison,
// so the input window is series[-(TIME_STEPS + N_FUTURE) : -N_FUTURE].
function prepareInput(series) {
  if (series.length < TIME_STEPS + N_FUTURE) {
    throw new Error(
      `Not enough data: need ${TIME_STEPS + N_FUTURE} steps (~${Math.round((TIME_STEPS + N_FUTURE) * 15 / 60 / 24)} days) but only have ${series.length}.`
    );
  }

  const lastWindow = series.slice(-(TIME_STEPS + N_FUTURE), -N_FUTURE).map(d => d.value);
  const scaled = minMaxScale(lastWindow);
  // TF.js tensor: shape [1, 1344, 1]
  return tf.tensor3d([scaled.map(v => [v])], [1, TIME_STEPS, 1]);
}


// ── Step 5: Build forecast timestamps ────────────────────────────────────────
// Timestamps start from the end of the INPUT window (N_FUTURE steps before the last point).
function buildForecastTimestamps(series) {
  const lastTs = series[series.length - N_FUTURE - 1].ts;
  return Array.from({ length: N_FUTURE }, (_, i) =>
    new Date(lastTs + INTERVAL_MS * (i + 1))
  );
}


// ── React Component ───────────────────────────────────────────────────────────
export function LSTMInference() {
  const [status, setStatus]       = useState("idle");   // idle | running | done | error
  const [errorMsg, setErrorMsg]   = useState("");
  const [forecast, setForecast]   = useState(null);     // { times, values, lastWindow }

  const runInference = async () => {
    try {
      setStatus("running");
      setErrorMsg("");

      // Guard: LDES data must be loaded first
      if (ldesState.count === 0) {
        throw new Error("No LDES data loaded yet. Wait for LDESClientCard to finish fetching.");
      }

      // 1. Extract from ldesState (same as datavisualization.jsx)
      setStatus("Extracting sensor data from ldesState...");
      const sensorDataMap = extractSensorData();
      const activeSensors = Object.keys(sensorDataMap);
      if (activeSensors.length === 0) {
        throw new Error("No target sensor data found in ldesState.");
      }

      // 2. Average + resample
      setStatus("Building average conductivity series...");
      const series = buildAverageSeries(sensorDataMap);

      // 3. Prepare input tensor (1, 1344, 1)
      setStatus("Preparing input window...");
      const inputTensor = prepareInput(series);

      // 4. Load TF.js model
      setStatus("Loading model...");
      //const model = await tf.loadLayersModel(MODEL_URL);
      const model = await tf.loadGraphModel(MODEL_URL);

      // 5. Run inference
      setStatus("Running inference...");
      const outputTensor   = await model.executeAsync({ Identity: inputTensor });
      const scaledForecast = await outputTensor.data();
    //   const outputTensor   = model.predict(inputTensor);
    //   const scaledForecast = await outputTensor.data(); // Float32Array of length 288
      
        

      // 6. Inverse-transform back to μS/cm
      const forecastValues = minMaxInverse(Array.from(scaledForecast));
      const forecastTimes  = buildForecastTimestamps(series);

      // Observed input window (last 2 weeks before the forecast starts)
      const lastWindowData = series.slice(-(TIME_STEPS + N_FUTURE), -N_FUTURE).map(d => [
        new Date(d.ts).toISOString(), d.value
      ]);

      // Ground truth: the real values that occurred during the forecast window
      const actualWindowData = series.slice(-N_FUTURE).map(d => [
        new Date(d.ts).toISOString(), d.value
      ]);

      setForecast({ times: forecastTimes, values: forecastValues, lastWindowData, actualWindowData });
      setStatus("done");

      // Cleanup tensors
      inputTensor.dispose();
      outputTensor.dispose();

    } catch (err) {
      console.error(err);
      setErrorMsg(err.message);
      setStatus("error");
    }
  };

  // ── Chart config ────────────────────────────────────────────────────────────
  const getChartOption = () => {
    if (!forecast) return {};

    const forecastSeries = forecast.times.map((t, i) => [
      t.toISOString(), forecast.values[i]
    ]);

    return {
      title: { text: "72-Hour Conductivity Forecast", left: "center", top: 10 },
      tooltip: { trigger: "axis", axisPointer: { type: "cross" } },
      legend: {
        data: ["Observed (last 2 weeks)", "Forecast (72 h)", "Actual (72 h)"],
        bottom: 50
      },
      grid: { left: "5%", right: "5%", bottom: "22%", containLabel: true },
      xAxis: {
        type: "time",
        name: "Date",
        nameLocation: "middle",
        nameGap: 35
      },
      yAxis: {
        type: "value",
        name: "μS/cm",
        nameLocation: "middle",
        nameGap: 50,
        min: 13900,
        max: 19500
      },
      dataZoom: [
        { type: "slider", xAxisIndex: 0, filterMode: "filter" },
        { type: "inside", xAxisIndex: 0 }
      ],
      series: [
        {
          name: "Observed (last 2 weeks)",
          type: "line",
          data: forecast.lastWindowData,
          showSymbol: false,
          lineStyle: { color: "#5470c6", width: 1.5 }
        },
        {
          name: "Forecast (72 h)",
          type: "line",
          data: forecastSeries,
          showSymbol: false,
          lineStyle: { color: "#ee6666", width: 2, type: "dashed" }
        },
        {
          name: "Actual (72 h)",
          type: "line",
          data: forecast.actualWindowData,
          showSymbol: false,
          lineStyle: { color: "#91cc75", width: 2 }
        }
      ]
    };
  };

  // ── Milestone summary (24h / 48h / 72h) ─────────────────────────────────────
  const milestones = forecast
    ? [
        { label: "+24 h", idx: 95 },
        { label: "+48 h", idx: 191 },
        { label: "+72 h", idx: 287 },
      ].map(m => ({
        label: m.label,
        time: forecast.times[m.idx]?.toLocaleString(),
        forecast: forecast.values[m.idx]?.toFixed(2),
        actual: forecast.actualWindowData[m.idx]?.[1]?.toFixed(2)
      }))
    : [];

  return (
    <div style={{ padding: "20px", border: "1px solid #ddd", borderRadius: "12px", background: "#fff" }}>

      {/* Header row */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
        <h3 style={{ margin: 0 }}>LSTM Forecast — 72 h ahead</h3>
        <button
          onClick={runInference}
          disabled={status === "running"}
          style={{
            padding: "10px 20px",
            backgroundColor: status === "running" ? "#aaa" : "#6f42c1",
            color: "white",
            border: "none",
            borderRadius: "5px",
            cursor: status === "running" ? "not-allowed" : "pointer"
          }}
        >
          {status === "running" ? "Running..." : "Run Inference"}
        </button>
      </div>

      {/* Status message */}
      {status !== "idle" && status !== "done" && status !== "error" && (
        <p style={{ color: "#6f42c1", fontSize: "13px" }}>⏳ {status}</p>
      )}
      {status === "error" && (
        <p style={{ color: "#dc3545", fontSize: "13px" }}>❌ {errorMsg}</p>
      )}

      {/* Milestone summary cards */}
      {forecast && (
        <div style={{ display: "flex", gap: "12px", marginBottom: "16px" }}>
          {milestones.map(m => (
            <div key={m.label} style={{
              flex: 1, padding: "12px", borderRadius: "8px",
              background: "#fff5f5", border: "1px solid #f5c2c2", textAlign: "center"
            }}>
              <div style={{ fontSize: "12px", color: "#888", marginBottom: "6px" }}>{m.label}</div>
              <div style={{ fontSize: "11px", color: "#aaa", marginBottom: "2px" }}>Forecast</div>
              <div style={{ fontSize: "18px", fontWeight: "bold", color: "#ee6666" }}>{m.forecast}</div>
              <div style={{ fontSize: "11px", color: "#aaa", marginTop: "6px", marginBottom: "2px" }}>Actual</div>
              <div style={{ fontSize: "18px", fontWeight: "bold", color: "#91cc75" }}>{m.actual ?? "—"}</div>
              <div style={{ fontSize: "11px", color: "#aaa" }}>μS/cm</div>
              <div style={{ fontSize: "10px", color: "#ccc", marginTop: "4px" }}>{m.time}</div>
            </div>
          ))}
        </div>
      )}

      {/* Chart */}
      {forecast ? (
        <ReactECharts
          option={getChartOption()}
          style={{ height: "500px", width: "100%" }}
          notMerge={true}
        />
      ) : (
        <div style={{
          height: "500px", display: "flex", flexDirection: "column",
          alignItems: "center", justifyContent: "center",
          background: "#fcfcfc", border: "1px dashed #ccc", borderRadius: "8px"
        }}>
          <p style={{ color: "#888" }}>
            Click "Run Inference" to generate a 72-hour forecast from loaded sensor data.
          </p>
          <p style={{ color: "#bbb", fontSize: "12px" }}>
            Requires LDESClientCard to have finished fetching first.
          </p>
        </div>
      )}

      {/* Note about scaler and model conversion */}
      <details style={{ marginTop: "16px", fontSize: "12px", color: "#888" }}>
        <summary style={{ cursor: "pointer" }}>Setup notes</summary>
        <ol style={{ marginTop: "8px", lineHeight: "1.8" }}>
          <li>
            <strong>Convert the model</strong> to TF.js format once in Python:
            <pre style={{ background: "#f8f8f8", padding: "8px", borderRadius: "4px" }}>
{`pip install tensorflowjs
tensorflowjs_converter --input_format=keras \\
  forecaster_v2.keras \\
  public/models/forecaster_v2/`}
            </pre>
          </li>
          <li>
            <strong>Export scaler params</strong> from Python and update <code>SCALER_MIN</code> / <code>SCALER_MAX</code> at the top of this file:
            <pre style={{ background: "#f8f8f8", padding: "8px", borderRadius: "4px" }}>
{`import joblib
s = joblib.load("scaler_v2.pkl")
print(s.data_min_[0], s.data_max_[0])`}
            </pre>
          </li>
        </ol>
      </details>
    </div>
  );
}
