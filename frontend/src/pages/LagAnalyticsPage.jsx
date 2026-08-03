import { useEffect, useMemo, useState } from 'react'
import ReactECharts from 'echarts-for-react'
import './LagAnalyticsPage.css'

const ANALYTICS_API = import.meta.env.VITE_ANALYTICS_API_URL || 'http://localhost:8010'

function ErrorNotice({ message }) {
  if (!message) return null
  return <div className="analytics-error"><b>Attention needed</b><span>{message}</span></div>
}

function Metric({ label, value, detail }) {
  return <div className="analytics-metric"><span>{label}</span><strong>{value ?? '—'}</strong>{detail && <small>{detail}</small>}</div>
}

function TimeSeriesChart({ series, title = 'Aligned sensor observations' }) {
  const option = useMemo(() => ({
    animation: false,
    color: ['#1b8f7a', '#2477a7', '#d08a3d', '#7f68b5', '#bf5b63'],
    tooltip: { trigger: 'axis' },
    legend: { type: 'scroll', top: 4, textStyle: { color: '#536f76' } },
    grid: { top: 50, left: 58, right: 24, bottom: 50 },
    xAxis: { type: 'time', axisLabel: { color: '#71878c' }, splitLine: { show: false } },
    yAxis: { type: 'value', name: 'Conductivity (mS/cm)', nameTextStyle: { color: '#71878c' }, axisLabel: { color: '#71878c' }, splitLine: { lineStyle: { color: '#edf2f3' } } },
    series: (series || []).map((item) => ({ name: item.label, type: 'line', showSymbol: false, sampling: 'lttb', data: item.points, lineStyle: { width: 1.8 } })),
  }), [series])
  return <div className="analytics-chart"><h4>{title}</h4><ReactECharts option={option} style={{ height: 360 }} /></div>
}

function LagChart({ result }) {
  const option = useMemo(() => ({
    animation: false,
    color: ['#1b8f7a', '#2477a7', '#d08a3d', '#7f68b5'],
    tooltip: { trigger: 'axis' },
    legend: { type: 'scroll', top: 4 },
    grid: { top: 50, left: 55, right: 22, bottom: 45 },
    xAxis: { type: 'value', name: 'Lag (hours)', axisLabel: { color: '#71878c' } },
    yAxis: { type: 'value', name: 'Correlation', min: -1, max: 1, axisLabel: { color: '#71878c' }, splitLine: { lineStyle: { color: '#edf2f3' } } },
    series: (result?.results || []).map((item) => ({ name: item.label, type: 'line', showSymbol: false, data: item.profile, markPoint: { symbolSize: 42, data: [{ coord: [item.best_lag_hours, item.correlation], value: `${item.best_lag_hours}h` }] } })),
  }), [result])
  return <div className="analytics-chart"><h4>Causally constrained cross-correlation profiles</h4><ReactECharts option={option} style={{ height: 350 }} /></div>
}

function ForecastChart({ points, title }) {
  const option = useMemo(() => ({
    animation: false,
    color: ['#173e48', '#42bda5'],
    tooltip: { trigger: 'axis' },
    legend: { top: 4 },
    grid: { top: 48, left: 58, right: 24, bottom: 48 },
    xAxis: { type: 'time', axisLabel: { color: '#71878c' } },
    yAxis: { type: 'value', name: 'Conductivity', axisLabel: { color: '#71878c' }, splitLine: { lineStyle: { color: '#edf2f3' } } },
    series: [
      { name: 'Observed', type: 'line', showSymbol: false, data: (points || []).map((point) => [point.time, point.actual]), lineStyle: { width: 1.8 } },
      { name: 'Predicted', type: 'line', showSymbol: false, data: (points || []).map((point) => [point.time, point.predicted]), lineStyle: { width: 2 } },
    ],
  }), [points])
  return <div className="analytics-chart"><h4>{title}</h4><ReactECharts option={option} style={{ height: 350 }} /></div>
}

function MatrixProfileChart({ result }) {
  const option = useMemo(() => ({
    animation: false,
    color: ['#7d68b4', '#178d82'],
    tooltip: { trigger: 'axis' },
    legend: { top: 4 },
    grid: { top: 48, left: 58, right: 24, bottom: 48 },
    xAxis: { type: 'time', axisLabel: { color: '#71878c' } },
    yAxis: { type: 'value', name: 'Profile distance', axisLabel: { color: '#71878c' }, splitLine: { lineStyle: { color: '#edf2f3' } } },
    series: [
      { name: '1-dimensional', type: 'line', showSymbol: false, data: result?.one_dimensional || [] },
      { name: `${result?.dimensions || 0}-dimensional`, type: 'line', showSymbol: false, data: result?.multidimensional || [], lineStyle: { width: 2 } },
    ],
  }), [result])
  return <div className="analytics-chart"><h4>Matrix-profile distance through time</h4><ReactECharts option={option} style={{ height: 350 }} /></div>
}

function Stage({ number, title, description, running, busy, completed, error, onRun, children, controls }) {
  return <article className={`analytics-stage ${completed ? 'completed' : ''}`}>
    <div className="analytics-stage-head">
      <span className="analytics-step">{String(number).padStart(2, '0')}</span>
      <div><h3>{title}</h3><p>{description}</p></div>
      <span className={`analytics-stage-status ${completed ? 'done' : ''}`}>{completed ? 'Output ready' : 'Ready'}</span>
      <button className="primary-button" disabled={busy} onClick={onRun}>{running ? 'Running…' : '▶ Run stage'}</button>
    </div>
    {controls && <div className="analytics-inline-controls">{controls}</div>}
    {(error || children) && <div className="analytics-output"><ErrorNotice message={error} />{children}</div>}
  </article>
}

export default function LagAnalyticsPage() {
  const [health, setHealth] = useState(null)
  const [graphs, setGraphs] = useState([])
  const [graph, setGraph] = useState('http://example.com/Gent-Terneuzen')
  const [sensors, setSensors] = useState([])
  const [target, setTarget] = useState('')
  const [upstream, setUpstream] = useState([])
  const [resampleMinutes, setResampleMinutes] = useState(15)
  const [observationLimit, setObservationLimit] = useState(50000)
  const [maxLagHours, setMaxLagHours] = useState(48)
  const [model, setModel] = useState('xgboost')
  const [epochs, setEpochs] = useState(3)
  const [matrixWindow, setMatrixWindow] = useState(24)
  const [results, setResults] = useState({})
  const [errors, setErrors] = useState({})
  const [running, setRunning] = useState('')
  const [catalogError, setCatalogError] = useState('')

  useEffect(() => {
    let cancelled = false
    async function loadService() {
      try {
        const [healthResponse, graphsResponse] = await Promise.all([
          fetch(`${ANALYTICS_API}/api/health`),
          fetch(`${ANALYTICS_API}/api/graphs`),
        ])
        if (!healthResponse.ok || !graphsResponse.ok) throw new Error('The analytics service did not return a valid response.')
        const healthResult = await healthResponse.json()
        const graphResult = await graphsResponse.json()
        if (cancelled) return
        setHealth(healthResult)
        setGraphs(graphResult.graphs || [])
        const preferred = (graphResult.graphs || []).includes(graphResult.default) ? graphResult.default : graphResult.graphs?.[0] || graphResult.default
        if (preferred) setGraph(preferred)
        setCatalogError('')
      } catch (error) {
        if (!cancelled) setCatalogError(`${error.message} Start it with: python -m uvicorn lag_analytics_workspace.server:app --reload --port 8010`)
      }
    }
    void loadService()
    return () => { cancelled = true }
  }, [])

  useEffect(() => {
    if (!graph) return
    let cancelled = false
    async function loadSensors() {
      try {
        const response = await fetch(`${ANALYTICS_API}/api/sensors?graph_uri=${encodeURIComponent(graph)}`)
        const value = await response.json()
        if (!response.ok) throw new Error(value.detail || 'Could not load sensors from Fuseki.')
        if (cancelled) return
        const available = value.sensors || []
        setSensors(available)
        const defaultTarget = available.find((sensor) => sensor.uri.endsWith('/111111111')) || available.at(-1)
        setTarget(defaultTarget?.uri || '')
        setUpstream(available.filter((sensor) => sensor.uri !== defaultTarget?.uri).slice(0, 4).map((sensor) => sensor.uri))
        setResults({})
        setErrors({})
        setCatalogError('')
      } catch (error) {
        if (!cancelled) setCatalogError(error.message)
      }
    }
    void loadSensors()
    return () => { cancelled = true }
  }, [graph])

  const commonRequest = {
    graph_uri: graph,
    target_sensor: target,
    upstream_sensors: upstream,
    resample_minutes: Number(resampleMinutes),
    observation_limit: Number(observationLimit),
    max_lag_hours: Number(maxLagHours),
  }

  async function runStage(id, endpoint, extra = {}) {
    if (!target || upstream.length === 0) {
      setErrors((current) => ({ ...current, [id]: 'Choose one target and at least one upstream sensor.' }))
      return
    }
    setRunning(id)
    setErrors((current) => ({ ...current, [id]: '' }))
    try {
      const response = await fetch(`${ANALYTICS_API}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...commonRequest, ...extra }),
      })
      const value = await response.json()
      if (!response.ok) throw new Error(value.detail || 'The analysis could not be completed.')
      setResults((current) => ({ ...current, [id]: value }))
    } catch (error) {
      setErrors((current) => ({ ...current, [id]: error.message }))
    } finally {
      setRunning('')
    }
  }

  function toggleUpstream(uri) {
    setUpstream((current) => current.includes(uri) ? current.filter((item) => item !== uri) : [...current, uri])
    setResults({})
  }

  return <section className="analytics-workspace">
    <div className="analytics-intro">
      <div><p className="eyebrow">Fuseki time-series laboratory</p><h2>Lag & predictive analytics</h2><p>Explore canal propagation delays, compare forecasting techniques, and discover repeating multivariate patterns using live SOSA observations.</p></div>
      <div className={`analytics-service ${health?.fuseki_connected ? 'online' : 'offline'}`}><i /><div><strong>{health?.fuseki_connected ? 'Fuseki connected' : 'Service unavailable'}</strong><small>{health?.fuseki_query_endpoint || 'Waiting for analytics API'}</small></div></div>
    </div>
    <ErrorNotice message={catalogError} />

    <div className="analytics-layout">
      <aside className="analytics-controls">
        <div className="analytics-control-title"><span>Experiment setup</span><small>Shared by every stage</small></div>
        <label>Named graph<select value={graph} onChange={(event) => setGraph(event.target.value)}>{graphs.length === 0 && <option value={graph}>{graph}</option>}{graphs.map((item) => <option key={item} value={item}>{item}</option>)}</select></label>
        <label>Prediction target<select value={target} onChange={(event) => { setTarget(event.target.value); setUpstream((current) => current.filter((uri) => uri !== event.target.value)); setResults({}) }}>{sensors.map((sensor) => <option key={sensor.uri} value={sensor.uri}>{sensor.label}</option>)}</select></label>
        <fieldset><legend>Upstream sensors <span>{upstream.length} selected</span></legend>{sensors.filter((sensor) => sensor.uri !== target).map((sensor) => <label className="analytics-check" key={sensor.uri}><input type="checkbox" checked={upstream.includes(sensor.uri)} onChange={() => toggleUpstream(sensor.uri)} /><span><b>{sensor.label}</b><small>{sensor.observations.toLocaleString()} observations</small></span></label>)}</fieldset>
        <div className="analytics-control-grid"><label>Grid interval<select value={resampleMinutes} onChange={(event) => setResampleMinutes(event.target.value)}><option value="15">15 minutes</option><option value="30">30 minutes</option><option value="60">1 hour</option></select></label><label>Max lag<input type="number" min="1" max="168" value={maxLagHours} onChange={(event) => setMaxLagHours(event.target.value)} /><span className="input-suffix">hours</span></label></div>
        <label>Fuseki row limit<input type="number" min="100" max="250000" step="1000" value={observationLimit} onChange={(event) => setObservationLimit(event.target.value)} /></label>
        <div className="analytics-source-note"><b>Read-only source</b><span>Every run queries Apache Jena Fuseki. No pipeline files or graph data are changed.</span></div>
      </aside>

      <div className="analytics-stages">
        <Stage number={1} title="Import & visualize" description="Load SOSA observations from the selected Fuseki named graph, pivot by sensor, resample, and interpolate the aligned grid." running={running === 'data'} busy={Boolean(running)} completed={Boolean(results.data)} error={errors.data} onRun={() => runStage('data', '/api/data')}>
          {results.data && <><div className="analytics-metrics"><Metric label="Source observations" value={results.data.raw_rows.toLocaleString()} /><Metric label="Aligned intervals" value={results.data.prepared_rows.toLocaleString()} /><Metric label="Sensors" value={results.data.sensor_count} /><Metric label="Canonical unit" value={results.data.canonical_unit} /></div><div className="analytics-unit-report"><div><b>Unit normalization applied before analysis</b><span>Every chart and model below receives conductivity in mS/cm.</span></div>{results.data.unit_normalization.map((item) => <div className="analytics-unit-row" key={item.sensor}><strong>{item.label}</strong><span>{item.methods.join(', ')}</span><small>{item.legacy_graph_repair ? 'Legacy graph signature detected' : 'QUDT metadata'}</small></div>)}</div><div className="analytics-period"><span>{new Date(results.data.start_time).toLocaleString()}</span><i /><span>{new Date(results.data.end_time).toLocaleString()}</span></div><TimeSeriesChart series={results.data.series} /></>}
        </Stage>

        <Stage number={2} title="Propagation lag analysis" description="Remove the daily baseline, smooth instrument noise, and search each station's physically plausible cross-correlation window." running={running === 'lag'} busy={Boolean(running)} completed={Boolean(results.lag)} error={errors.lag} onRun={() => runStage('lag', '/api/lag')}>
          {results.lag && <><div className="analytics-lag-grid">{results.lag.results.map((item) => <div key={item.sensor}><span>{item.label} → {results.lag.target_label}</span><strong>{item.best_lag_hours} h</strong><small>r = {item.correlation ?? 'n/a'} · searched {item.search_window_hours.join('–')} h</small></div>)}</div><LagChart result={results.lag} /></>}
        </Stage>

        <Stage number={3} title="Machine-learning forecast" description="Build lag-aware delta features and evaluate a chronological holdout using the notebook's XGBoost, SVR, or MLP techniques." running={running === 'ml'} busy={Boolean(running)} completed={Boolean(results.ml)} error={errors.ml} onRun={() => runStage('ml', '/api/machine-learning', { model_name: model, forecast_horizon_hours: 1 })} controls={<label>Estimator<select value={model} onChange={(event) => setModel(event.target.value)}><option value="xgboost">XGBoost</option><option value="svr">Support vector regression</option><option value="mlp">Multilayer perceptron</option></select></label>}>
          {results.ml && <><div className="analytics-metrics"><Metric label="MAE" value={results.ml.metrics.mae} /><Metric label="RMSE" value={results.ml.metrics.rmse} /><Metric label="R²" value={results.ml.metrics.r2} /><Metric label="Holdout" value={`${results.ml.test_samples} rows`} detail={results.ml.model_label} /></div><ForecastChart points={results.ml.predictions} title="Observed versus reconstructed one-hour forecast" /><div className="analytics-importance"><h4>Feature influence</h4>{results.ml.feature_importance.map((item) => <div key={item.feature}><span>{item.feature.replaceAll('_', ' ')}</span><i><b style={{ width: `${Math.max(2, Math.abs(item.importance || 0) * 100)}%` }} /></i><strong>{item.importance}</strong></div>)}</div></>}
        </Stage>

        <Stage number={4} title="Deep-learning forecast" description="Train the notebook-inspired LSTM autoencoder, attach a forecast head, and fine-tune it on the chronological sensor sequences." running={running === 'deep'} busy={Boolean(running)} completed={Boolean(results.deep)} error={errors.deep} onRun={() => runStage('deep', '/api/deep-learning', { epochs: Number(epochs), lookback_hours: 48, forecast_horizon_hours: 4 })} controls={<label>Epochs per phase<input type="number" min="1" max="20" value={epochs} onChange={(event) => setEpochs(event.target.value)} /></label>}>
          {results.deep && <><div className="analytics-metrics"><Metric label="MAE" value={results.deep.metrics.mae} /><Metric label="RMSE" value={results.deep.metrics.rmse} /><Metric label="Training sequences" value={results.deep.train_sequences.toLocaleString()} /><Metric label="Architecture" value="LSTM" detail={`${results.deep.lookback_hours}h lookback → ${results.deep.forecast_horizon_hours}h`} /></div><ForecastChart points={results.deep.forecast} title="Latest four-hour LSTM forecast horizon" /></>}
        </Stage>

        <Stage number={5} title="Multidimensional matrix profile" description="Measure repeating patterns jointly across the selected canal sensors; low distances are motifs and high distances are unusual discords." running={running === 'matrix'} busy={Boolean(running)} completed={Boolean(results.matrix)} error={errors.matrix} onRun={() => runStage('matrix', '/api/matrix-profile', { window_hours: Number(matrixWindow) })} controls={<label>Pattern window<input type="number" min="1" max="168" value={matrixWindow} onChange={(event) => setMatrixWindow(event.target.value)} /><span className="input-suffix">hours</span></label>}>
          {results.matrix && <><div className="analytics-metrics"><Metric label="Dimensions" value={results.matrix.dimensions} /><Metric label="Window" value={`${results.matrix.window_hours} h`} detail={`${results.matrix.window_points} effective points`} /><Metric label="Best motif" value={results.matrix.motif.distance} detail={new Date(results.matrix.motif.start_time).toLocaleString()} /><Metric label="Strongest discord" value={results.matrix.discord.distance} detail={new Date(results.matrix.discord.start_time).toLocaleString()} /></div><MatrixProfileChart result={results.matrix} /><div className="analytics-insight"><b>Most repeated sequence</b><span>{new Date(results.matrix.motif.start_time).toLocaleString()} matches {new Date(results.matrix.motif.match_time).toLocaleString()}.</span></div></>}
        </Stage>
      </div>
    </div>
  </section>
}
