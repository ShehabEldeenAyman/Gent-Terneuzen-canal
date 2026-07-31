import { useState } from 'react'
import { CircleMarker, MapContainer, Polyline, TileLayer, Tooltip } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import './UseCasePage.css'

const stations = [
  {
    name: 'Zevenaarhaven',
    place: 'Terneuzen',
    country: 'NL',
    code: 'IOW51',
    position: [51.3032958, 3.8365264],
    reach: 'Sea-side station',
    timeSeries: 4,
    description: 'The northern monitoring point, closest to the Terneuzen locks and the first signal of inland salt movement.',
  },
  {
    name: 'Autrichehaven',
    place: 'Westdorpe',
    country: 'NL',
    code: 'IOW50',
    position: [51.2636224, 3.8463052],
    reach: 'Northern canal reach',
    timeSeries: 4,
    description: 'A Dutch canal station that helps measure how quickly a conductivity rise travels south from Terneuzen.',
  },
  {
    name: 'Rodenhuizedok',
    place: 'Ghent',
    country: 'BE',
    code: 'IOW49',
    position: [51.1461914, 3.7893741],
    reach: 'Industrial canal reach',
    timeSeries: 4,
    description: 'A Belgian industrial-port station used to observe whether the salt wedge reaches sensitive inland users.',
  },
  {
    name: 'Grootdok',
    place: 'Ghent',
    country: 'BE',
    code: 'IOW48',
    position: [51.0870045, 3.7351871],
    reach: 'Inland station',
    timeSeries: 4,
    description: 'The southernmost station in the network, providing the inland reference point for comparison and alerting.',
  },
]

const canalPath = [
  [51.345, 3.824],
  stations[0].position,
  stations[1].position,
  [51.205, 3.822],
  stations[2].position,
  stations[3].position,
]

const applications = [
  ['Forecast salinity', 'Combine canal observations with tidal data to anticipate conductivity peaks before they reach water intakes.'],
  ['Alert operators', 'Trigger operational warnings when normalized water quality exceeds the limit of an industrial process.'],
  ['Track long-term change', 'Assess whether inland salt intrusion is increasing with sea-level rise or changing lock operations.'],
  ['Report across borders', 'Use consistent EC20 measurements to support shared Belgian–Dutch environmental reporting.'],
]

function UseCasePage({ onOpenPipeline }) {
  const [activeStation, setActiveStation] = useState(stations[0])

  return <div className="usecase-page">
    <section className="usecase-hero">
      <div className="usecase-hero-copy">
        <p className="eyebrow">Gent–Terneuzen Canal use case</p>
        <h2>Understand and anticipate salt intrusion.</h2>
        <p>Salt water from the North Sea can move inland through the canal and affect industrial water users. This use case turns live conductivity observations into comparable, traceable information about where that salt wedge is—and where it may travel next.</p>
        <div className="usecase-actions">
          <button className="primary-button" onClick={onOpenPipeline}>Open the processing pipeline →</button>
          <span>BE / NL · 4 monitoring stations</span>
        </div>
      </div>
      <div className="usecase-hero-figure" aria-label="Salt intrusion monitoring concept">
        <div className="sea-label"><span /> North Sea</div>
        <div className="canal-line"><i /><i /><i /><i /></div>
        <div className="flow-label">salt signal <b>travels inland</b> ↓</div>
      </div>
    </section>

    <section className="usecase-summary-grid" aria-label="Use case summary">
      <article><span>01</span><div><strong>Observe</strong><p>VITO sensors publish live conductivity measurements through waterinfo.be.</p></div></article>
      <article><span>02</span><div><strong>Normalize</strong><p>EC20 corrects readings to 20°C so measurements can be compared over time.</p></div></article>
      <article><span>03</span><div><strong>Anticipate</strong><p>Time lags and spatial gradients reveal how salinity propagates between stations.</p></div></article>
    </section>

    <section className="usecase-map-section">
      <div className="usecase-section-heading">
        <div><p className="eyebrow">Monitoring network</p><h2>Follow the canal from sea to city</h2></div>
        <p>Select a station on the map or in the route list to explore its role.</p>
      </div>
      <div className="usecase-map-layout">
        <div className="canal-map">
          <MapContainer bounds={[[51.06, 3.69], [51.36, 3.89]]} boundsOptions={{ padding: [24, 24] }} scrollWheelZoom={false}>
            <TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
            <Polyline positions={canalPath} pathOptions={{ color: '#1b7f8c', weight: 6, opacity: 0.72 }} />
            <Polyline positions={canalPath.slice(0, 4)} pathOptions={{ color: '#e77755', weight: 3, opacity: 0.85, dashArray: '8 10' }} />
            {stations.map((station, index) => <CircleMarker
              key={station.code}
              center={station.position}
              radius={activeStation.code === station.code ? 10 : 7}
              pathOptions={{ color: '#ffffff', weight: 3, fillColor: index < 2 ? '#e77755' : '#38bca4', fillOpacity: 1 }}
              eventHandlers={{ click: () => setActiveStation(station) }}
            ><Tooltip direction="top" offset={[0, -8]}><strong>{station.name}</strong><br />{station.code} · {station.country}</Tooltip></CircleMarker>)}
          </MapContainer>
          <div className="map-legend"><span><i className="salt" /> Salt-entry reach</span><span><i className="fresh" /> Inland monitoring</span></div>
        </div>
        <aside className="station-explorer">
          <div className="station-detail">
            <p>{activeStation.reach}</p>
            <h3>{activeStation.name}</h3>
            <span>{activeStation.place}, {activeStation.country}</span>
            <dl><div><dt>Station code</dt><dd>{activeStation.code}</dd></div><div><dt>Time series</dt><dd>{activeStation.timeSeries}</dd></div></dl>
            <p className="station-description">{activeStation.description}</p>
          </div>
          <div className="station-route" aria-label="Monitoring stations from north to south">
            {stations.map((station, index) => <button className={activeStation.code === station.code ? 'active' : ''} key={station.code} onClick={() => setActiveStation(station)}>
              <span>{String(index + 1).padStart(2, '0')}</span><div><strong>{station.name}</strong><small>{station.code} · {station.country}</small></div>
            </button>)}
          </div>
          <small className="map-note">Map positions provide geographic context; pipeline station identifiers remain the authoritative reference.</small>
        </aside>
      </div>
    </section>

    <section className="analysis-section">
      <div className="usecase-section-heading">
        <div><p className="eyebrow">Spatial–temporal propagation</p><h2>Turn four points into an early signal</h2></div>
        <p>Ordered stations make it possible to model movement, not just isolated measurements.</p>
      </div>
      <div className="analysis-grid">
        <article><span>t − Δ</span><h3>Time-lagged features</h3><p>A conductivity spike at the sea-side station will not reach the next station immediately. Cross-correlation can estimate that travel time and turn an earlier upstream value into a predictor.</p></article>
        <article><span>C₁ − C₂</span><h3>Spatial gradients</h3><p>The difference between adjacent stations shows where conductivity is rising most sharply and how far the salt signal has progressed along the canal.</p></article>
      </div>
    </section>

    <section className="application-section">
      <div className="usecase-section-heading"><div><p className="eyebrow">Operational goal</p><h2>From measurement to coordinated action</h2></div></div>
      <div className="application-grid">{applications.map(([title, description], index) => <article key={title}><span>0{index + 1}</span><h3>{title}</h3><p>{description}</p></article>)}</div>
    </section>
  </div>
}

export default UseCasePage
