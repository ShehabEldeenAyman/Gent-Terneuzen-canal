import { color } from 'echarts';
import React, { useState,useEffect } from 'react';
import 'leaflet/dist/leaflet.css';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';

  // 2. Styles for the inner layout
  const innerStyles = {
    container: {
      height: '100%',
      //backgroundColor: '#1523e0',
      borderRadius: '1em',
      display: 'flex',
      flexDirection: 'column',
      color: 'white',
      padding: '1rem',
      boxSizing: 'border-box'
    },
    subNavbar: {
      display: 'flex',
      alignItems: 'center',
      gap: '10px',
      marginBottom: '1rem',
      fontSize: '0.9rem'
    },
    divider: {
      width: '1px',
      height: '15px',
     // backgroundColor: 'rgba(255, 255, 255, 0.4)'
    },
    navItem: (isActive) => ({
      cursor: 'pointer',
      fontWeight: isActive ? 'bold' : 'normal',
      opacity: isActive ? 1 : 0.7,
      transition: 'opacity 0.2s',
      color: isActive ? '#000000' : '#000000',
    }),
    contentArea: {
      flexGrow: 1,
      backgroundColor: 'rgba(255, 255, 255, 0.1)',
      borderRadius: '0.5em',
      padding: '1rem',
      color: 'black',
    }
  };
  const headStyles = {
    title: {
      textAlign: 'center',        // Centers the H2
      fontSize: '1.4rem',         // Slightly larger for the header
      fontWeight: '700',
      marginBottom: '0',
      marginTop: '0',
    },
    description: {
      textAlign: 'justify',       // Justifies the body text
      fontSize: '0.85rem',        // Smaller text size as requested
      lineHeight: '1.5',          // Increases readability
      margin: '0',
      opacity: '0.95',            // Softens the white text slightly
    }
  };

export const MapCardHead = () => {


  return (
    <div >
      <h2 style={headStyles.title}>
        Mol Sluis / Kl Dessel–Kwaadmechelen
      </h2>
      <p style={headStyles.description}>
        At the Mol Sluis station on the Dessel–Kwaadmechelen Canal, two key 
        hydrological parameters — river stage and river discharge 
        — are continuously monitored by the Flemish Hydrological 
        Information Centre. These two datasets describe complementary 
        aspects of the canal’s behavior: the water level (stage) in meters and the 
        flow rate (discharge) in cubic meters per second. Integrating these 
        parameters provides a richer, multidimensional view of the canal’s condition, 
        essential for both operational management and scientific analysis. Each 
        record contains timestamps in UTC, the measured value, station coordinates, 
        and metadata identifying the provider and measurement type. 
      </p>
    </div>
  );
};

export const MapCardBody = () => {
  // 1. Local state for the sub-menu
  const [activeSubTab, setActiveSubTab] = useState('UseCase');
  const menuItems = ['UseCase', 'Parameters', 'Attributes', 'Map'];
const renderSubContent = () => {
    switch (activeSubTab) {
      case 'UseCase':
        return <UsecaseTab />;
      case 'Parameters':
        return <ParametersTab />;
      case 'Attributes':
        return <AttributesTab />;
      case 'Map':
        return <MapTab />;
      default:
        return <div><h3>Overview Content Placeholder</h3></div>;
    }
  };


  return (
    <div style={innerStyles.container}>
      {/* 3. Horizontal Sub-Navbar */}
      <div style={innerStyles.subNavbar}>
        {menuItems.map((item, index) => (
          <React.Fragment key={item}>
            <span 
              style={innerStyles.navItem(activeSubTab === item)}
              onClick={() => setActiveSubTab(item)}
            >
              {item}
            </span>
            {/* 4. Add vertical line between items, but not after the last one */}
            {index < menuItems.length - 1 && <div style={innerStyles.divider} />}
          </React.Fragment>
        ))}
      </div>

<div style={innerStyles.contentArea}>
        {renderSubContent()}
      </div>
    </div>
  );
};

const MapTab = () => {
  // Approximate coordinates for Mol Sluis / Dessel–Kwaadmechelen area
  const position = [51.1903, 5.1157]; 

  return (
    <div style={{ height: '400px', width: '100%', borderRadius: '8px', overflow: 'hidden' }}>
      <MapContainer 
        center={position} 
        zoom={13} 
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Marker position={position}>
          <Popup>
            <strong>Mol Sluis Station</strong> <br />
            Monitoring River Stage and Discharge. 
          </Popup>
        </Marker>
      </MapContainer>
    </div>
  );
};

const UsecaseTab = () => (
<div>
        <p style={headStyles.description}>
        For a water data scientist, this integrated dataset enables a complete monitoring and forecasting workflow. By aligning the stage and discharge data from the same location, the scientist can detect abnormal relationships — for example, sudden increases in water level without corresponding discharge changes, which might indicate a sluice malfunction or obstruction. The dataset also supports short-term forecasting of stage and flow, crucial for navigation safety, sluice operation scheduling, and flood risk management. Using statistical or machine learning models, future water levels and discharges can be predicted up to 72 hours. This helps operators anticipate peak flows, low-water conditions, or abrupt level changes that could affect shipping or infrastructure.
      </p>
              <p style={headStyles.description}>
Through this integration, the Mol Sluis dataset becomes more than a collection of raw measurements — it becomes an operational intelligence layer for canal management. It supports proactive decision-making by enabling early anomaly detection, improved calibration of hydraulic models, and automated alerts for critical thresholds. Ultimately, this unified dataset empowers the water data scientist to deliver insights that improve safety, efficiency, and resilience in the canal’s daily operations.      </p>
  </div>
);

const ParametersTab = () => (
  <div>
    <h3>River Stage (Water Level)</h3>
    <p style={headStyles.description}>The vertical distance from the water's surface to a fixed reference point on the riverbed. It is often measured in meters (m) or feet (ft). It indicates if the river is "running high" or "running low."  </p>
    <h3>River Discharge (Flow Rate)</h3>
    <p style={headStyles.description}>The amount of water passing through a specific point every second. It is calculated by multiplying the area of the river (width × depth) by velocity. It is measured in cubic meters per second (m^3/s) or cubic feet per second (cfs). If the Stage (height) increases, the Discharge (volume) also increases.  </p>
    <h3>Discharge Runoff</h3>
    <p style={headStyles.description}>The portion of rain (or snowmelt) didn't soak into the ground but instead "ran off" the surface and into the river. It is measured in  Liters per second (L/s). It helps understand how the surrounding land responds to a storm. If the land is paved or saturated, the runoff value will spike after it rains.  </p>

  </div>
);

const AttributesTab = () => {
  // Data extracted from the document 
  const tableData = [
    { column: "ts_id", example: "98536010", meaning: "The unique identifier for this time series (used to distinguish it from others in the database)." },
    { column: "timestamp", example: "2025-10-28T08:30:00.000Z", meaning: "The exact time the measurement was taken (in UTC, ISO 8601 format)." },
    { column: "req_timestamp", example: "(empty)", meaning: "Likely used to record when the data was requested or received. It’s empty here." },
    { column: "ts_value", example: "4.57", meaning: "The measured value — in this case, 4.57 meters." },
    { column: "station_latitude", example: "51.1983396964869", meaning: "Latitude of the measuring station (in decimal degrees)." },
    { column: "station_longitude", example: "3.80050336467076", meaning: "Longitude of the measuring station." },
    { column: "ts_name", example: "Pv", meaning: "Short name for the time series (possibly a sensor or parameter code)." },
    { column: "ts_shortname", example: "Cmd.Abs.Pv", meaning: "A concise technical name — “Command Absolute PV” or similar (depends on the system)." },
    { column: "station_no", example: "kgt04a-1066", meaning: "Station’s unique code within the system." },
    { column: "station_id", example: "156346", meaning: "Numerical ID for the station (database key)." },
    { column: "station_name", example: "Zelzate/Kl Gent-Terneuzen", meaning: "The name of the monitoring station (in this case, near Zelzate, Belgium, along the Ghent–Terneuzen Canal)." },
    { column: "stationparameter_name", example: "H", meaning: "The parameter code (here, “H” stands for Water Level / Stage Height)." },
    { column: "stationparameter_no", example: "H", meaning: "Duplicate code for the parameter." },
    { column: "stationparameter_longname", example: "River Stage", meaning: "The long description — the height of the water surface (e.g., in a river or canal)." },
    { column: "ts_unitname", example: "meter", meaning: "The unit of the measurement." },
    { column: "ts_unitsymbol", example: "m", meaning: "The symbol for the unit." },
    { column: "parametertype_id", example: "560", meaning: "Internal ID of the parameter type in the database." },
    { column: "parametertype_name", example: "H", meaning: "Name or code for the parameter type." },
    { column: "ts_path", example: "Zelzate/kgt04a-1066/H/Cmd.Abs.Pv", meaning: "Hierarchical path describing the data source: Station → Code → Parameter → Time series." },
    { column: "dataprovider", example: "MOW-HIC", meaning: "The organization providing the data. “MOW-HIC” stands for Flemish Ministry of Mobility and Public Works – Hydrologisch Informatiecentrum." }
  ];

  return (
    /* The wrapper prevents the table from expanding the parent container */
    <div style={styles.tableWrapper}>
      <table style={styles.table}>
        <thead>
          <tr style={styles.headerRow}>
            <th style={{...styles.th, width: '20%'}}>Column</th>
            <th style={{...styles.th, width: '25%'}}>Example Value</th>
            <th style={{...styles.th, width: '55%'}}>Meaning / Explanation</th>
          </tr>
        </thead>
        <tbody>
          {tableData.map((row, index) => (
            <tr key={index} style={index % 2 === 0 ? styles.evenRow : styles.oddRow}>
              <td style={{...styles.td, ...styles.codeColumn}}>{row.column}</td>
              <td style={styles.td}>{row.example}</td>
              <td style={styles.td}>{row.meaning}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

const styles = {
tableWrapper: {
    width: '100%',
    maxHeight: '400px',
    overflow: 'auto',
    borderRadius: '4px',
    border: '1px solid #ddd',
    // ADD THIS LINE BELOW:
    boxSizing: 'border-box', 
  },
  table: {
    width: '100%',
    borderCollapse: 'separate', // Better for rounded corners on wrappers
    borderSpacing: 0,
    fontSize: '0.85rem',
    tableLayout: 'fixed', // Force columns to respect width percentages
    backgroundColor: '#fff',
  },
  headerRow: {
    backgroundColor: '#f4f4f4',
    position: 'sticky', // Keeps header visible while scrolling
    top: 0,
    zIndex: 1,
  },
  th: {
    padding: '10px',
    textAlign: 'left',
    fontWeight: 'bold',
    color: '#333',
    borderBottom: '2px solid #ddd',
    borderRight: '1px solid #eee',
  },
  td: {
    padding: '8px 10px',
    borderBottom: '1px solid #eee',
    borderRight: '1px solid #eee',
    verticalAlign: 'top',
    wordWrap: 'break-word', // Ensures text wraps inside the cell
  },
  codeColumn: {
    fontFamily: 'monospace',
    fontWeight: '600',
    color: '#d63384',
  },
  evenRow: { backgroundColor: '#ffffff' },
  oddRow: { backgroundColor: '#fcfcfc' }
};