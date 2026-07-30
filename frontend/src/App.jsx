import { useState } from 'react'
import './App.css'

const API = import.meta.env.VITE_PIPELINE_API_URL || 'http://localhost:8000'
const PLAYGROUND = [
  {
    id: 'water-link', title: 'Water-Link conductivity',
    description: 'Clean the supplied workbook, map it to RDF, validate and align units, then create TSS and inferred RDF.',
    stages: [
      ['prepare', 'Prepare workbook', 'Clean the Water-Link Excel result sheet into a CSV.'],
      ['map', 'Map to RDF', 'Generate RML and transform the CSV into Turtle RDF.'],
      ['validate-input', 'Validate input', 'Check the source RDF against the MicroS/cm SHACL shape.'],
      ['align', 'Align units', 'Convert observations to milliSiemens per centimetre.'],
      ['validate-output', 'Validate output', 'Check the normalized RDF against the canonical SHACL shape.'],
      ['tss', 'Create TSS', 'Create Time Series Snippets from the RDF observations.'],
      ['reason', 'Run N3 rules', 'Generate inferred triples and quality annotations.'],
      ['ingest', 'Ingest to Virtuoso', 'Upload the normalized RDF to the configured named graph.'],
    ], results: {},
  },
  {
    id: 'waterinfo-conductivity', title: 'Waterinfo conductivity',
    description: 'Fetch conductivity measurements, then apply the same semantic quality pipeline.',
    stages: [
      ['fetch', 'Fetch measurements', 'Download the configured Waterinfo sensor series.'],
      ['prepare', 'Prepare CSV', 'Add Unix timestamps and normalize date formatting.'],
      ['map', 'Map to RDF', 'Generate RML and transform CSV measurements into Turtle RDF.'],
      ['validate-input', 'Validate input', 'Check source RDF against the MicroS/cm SHACL shape.'],
      ['align', 'Align units', 'Convert observations to milliSiemens per centimetre.'],
      ['validate-output', 'Validate output', 'Check normalized RDF against the canonical SHACL shape.'],
      ['tss', 'Create TSS', 'Create Time Series Snippets from the RDF observations.'],
      ['ingest', 'Ingest to Virtuoso', 'Upload normalized RDF to the configured named graph.'],
    ], results: {},
  },
]

function Output({ result }) {
  const [preview, setPreview] = useState(null)
  const [previewing, setPreviewing] = useState(false)

  async function showArtifact(path) {
    setPreviewing(true)
    try {
      const response = await fetch(`${API}/api/artifacts/${path}`)
      setPreview({ path, text: await response.text() })
    } finally {
      setPreviewing(false)
    }
  }

  if (!result) return <p className="empty">Run this stage to inspect its logs and generated artifacts.</p>
  return <div className={`output ${result.status}`}>
    <strong>{result.status === 'success' ? 'Completed' : 'Needs attention'}</strong>
    <span>{result.message} · {result.duration_seconds}s</span>
    {result.artifacts?.map((item) => <button className="artifact" key={item.path} disabled={!item.exists || previewing} onClick={() => showArtifact(item.path)}>{item.path} ({item.exists ? `${item.size.toLocaleString()} bytes` : 'not created'})</button>)}
    {result.log && <details><summary>Execution log</summary><pre>{result.log}</pre></details>}
    {preview && <details open><summary>{preview.path}</summary><pre>{preview.text}</pre></details>}
  </div>
}

function App() {
  const [useCases, setUseCases] = useState(PLAYGROUND)
  const [active, setActive] = useState('water-link')
  const [running, setRunning] = useState(null)
  const [error, setError] = useState('')

  async function load() {
    try {
      const response = await fetch(`${API}/api/use-cases`)
      if (!response.ok) throw new Error('The pipeline server is unavailable.')
      setUseCases(await response.json())
      setError('')
    } catch (err) { setError(`${err.message} Start it with: uvicorn pipeline.playground_server:app --reload --port 8000`) }
  }
  const useCase = useCases.find((item) => item.id === active) || useCases[0]

  async function runStage(stageId) {
    setRunning(stageId)
    try {
      const response = await fetch(`${API}/api/use-cases/${active}/stages/${stageId}`, { method: 'POST' })
      const result = await response.json()
      setUseCases((current) => current.map((item) => item.id === active ? { ...item, results: { ...item.results, [stageId]: result } } : item))
    } catch (err) { setError(`Could not run the stage: ${err.message}`) }
    finally { setRunning(null) }
  }

  return <main className="playground">
    <header>
      <p className="eyebrow">Gent–Terneuzen Canal</p>
      <h1>Pipeline Playground</h1>
      <p>Run each semantic-data stage deliberately, inspect its output, then continue when you are satisfied.</p>
    </header>
    {error && <aside className="notice">{error}</aside>}
    <nav aria-label="Use cases">{useCases.map((item) => <button className={item.id === active ? 'selected' : ''} key={item.id} onClick={() => setActive(item.id)}>{item.title}</button>)}</nav>
    {useCase && <section className="workflow">
      <div className="workflow-heading"><div><h2>{useCase.title}</h2><p>{useCase.description}</p></div><button className="refresh" onClick={load}>Refresh server state</button></div>
      <ol>{useCase.stages.map(([id, title, description], index) => <li key={id} className="stage">
        <div className="stage-number">{String(index + 1).padStart(2, '0')}</div>
        <div className="stage-content"><h3>{title}</h3><p>{description}</p><Output result={useCase.results?.[id]} /></div>
        <button className="run" disabled={running !== null} onClick={() => runStage(id)}>{running === id ? 'Running…' : 'Run stage'}</button>
      </li>)}</ol>
    </section>}
  </main>
}

export default App
