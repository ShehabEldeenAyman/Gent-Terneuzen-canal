import React, { useState,useEffect } from "react";
import ReactECharts from "echarts-for-react";
import { DataFactory } from "n3";
import { ldesState } from "./LDESClientCard";

const { namedNode } = DataFactory;

// 1. Configuration & Constants
const PREFIXES = {
  TSS: "https://w3id.org/tss#",
  RDF: "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
};

export const TARGET_SENSOR_IDS = ["289435042", "289429042", "289441042", "289423042"];

export const sensor_data = {
  sensorDataMap: {}, // { "sensorID": [[time, value], ...] }
  activeSensors: [] // List of sensor IDs we found data for
}

export function TestCard() {
  // We use an object to store data grouped by ID: { "sensorID": [[time, value], ...] }
  const [sensorDataMap, setSensorDataMap] = useState(sensor_data.sensorDataMap);
  const [activeSensors, setActiveSensors] = useState(sensor_data.activeSensors);

  // Whenever the internal state changes, sync it to the exported object
  useEffect(() => {
    sensor_data.sensorDataMap = sensorDataMap;
    sensor_data.activeSensors = activeSensors;
  }, [sensorDataMap, activeSensors]);

  /**
   * DATA PROCESSING LOGIC
   */
  const handleLoadData = () => {
    if (ldesState.count === 0) return;

    // A. Find all Snippets
    const snippetSubjects = ldesState.store
      .getQuads(null, namedNode(PREFIXES.RDF + "type"), namedNode(PREFIXES.TSS + "Snippet"), null)
      .map(q => q.subject.value);

    // Temporary storage for our data grouping
    const tempMap = {};
    const foundSensors = new Set();

    snippetSubjects.forEach(uri => {
      // B. Extract Sensor ID from URI
      // Pattern: .../waterinfo/{SENSOR_ID}/{DATE_CODE}
      const uriParts = uri.split('/');
      const waterInfoIndex = uriParts.indexOf('waterinfo');
      
      // The ID is the segment immediately following 'waterinfo'
      const extractedId = uriParts[waterInfoIndex + 1];

      // C. Filter: Only proceed if the ID is in our allowed list
      if (TARGET_SENSOR_IDS.includes(extractedId)) {
        foundSensors.add(extractedId);

        // Get the points for this specific URI
        const pointsRecord = ldesState.store.getQuads(
          namedNode(uri), 
          namedNode(PREFIXES.TSS + "points"), 
          null, 
          null
        )[0];

        const rawPoints = pointsRecord?.object.value;
        
        if (rawPoints) {
          const parsedPoints = JSON.parse(rawPoints);
          
          // Format as [time, value] for ECharts
          const formattedPoints = parsedPoints.map(p => [p.time, p.value]);

          // D. Grouping: Add these points to the specific sensor's array
          if (!tempMap[extractedId]) {
            tempMap[extractedId] = [];
          }
          tempMap[extractedId].push(...formattedPoints);
        }
      }
    });

    // E. Sort each sensor's data by time (required for clean line drawing)
    Object.keys(tempMap).forEach(id => {
      tempMap[id].sort((a, b) => new Date(a[0]) - new Date(b[0]));
    });

    // Update state to trigger UI refresh
    setSensorDataMap(tempMap);
    setActiveSensors(Array.from(foundSensors));
  };

  /**
   * CHART CONFIGURATION
   */
  const getOption = () => {
    // Dynamically create a series (line) for every sensor we found data for
    const series = activeSensors.map(id => ({
      name: `Sensor ${id}`,
      type: 'line',
      data: sensorDataMap[id],
      showSymbol: false,
      smooth: true,
      lineStyle: { width: 2 }
    }));

    return {
      title: {
        text: 'Conductivity Measurements by Sensor',
        left: 'center',
        top: 10
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' }
      },
      legend: {
        data: activeSensors.map(id => `Sensor ${id}`),
        bottom: 50 // Placed above the slider
      },
      grid: {
        left: '5%',
        right: '5%',
        bottom: '22%', // Extra room for the zoom slider
        containLabel: true
      },
      xAxis: {
        type: 'time',
        name: 'Date',
        nameLocation: 'middle',
        nameGap: 35
      },
      yAxis: {
        type: 'value',
        name: 'μS/cm',
        nameLocation: 'middle',
        nameGap: 50
      },
      dataZoom: [
        {
          type: 'slider', // The scrollbar at the bottom
          xAxisIndex: 0,
          filterMode: 'filter'
        },
        {
          type: 'inside', // Mouse wheel / pinch-to-zoom
          xAxisIndex: 0
        }
      ],
      series: series
    };
  };

  return (
    <div style={{ padding: "20px", border: "1px solid #ddd", borderRadius: "12px", background: "#fff" }}>
      <div style={{ marginBottom: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <button 
          onClick={handleLoadData} 
          style={{ 
            padding: '10px 20px', 
            backgroundColor: '#007bff', 
            color: 'white', 
            border: 'none', 
            borderRadius: '5px', 
            cursor: 'pointer' 
          }}
        >
          Load Sensor Data
        </button>
        <span style={{ fontSize: '14px', color: '#666' }}>
          Sensors Found: {activeSensors.length} / {TARGET_SENSOR_IDS.length}
        </span>
      </div>

      {activeSensors.length > 0 ? (
        <ReactECharts 
          option={getOption()} 
          style={{ height: '550px', width: '100%' }} 
          notMerge={true} // Ensures the chart refreshes fully when new data loads
        />
      ) : (
        <div style={{ 
          height: '550px', 
          display: 'flex', 
          flexDirection: 'column',
          alignItems: 'center', 
          justifyContent: 'center', 
          background: '#fcfcfc',
          border: '1px dashed #ccc',
          borderRadius: '8px'
        }}>
          <p style={{ color: '#888' }}>Ready to load. Click "Load Sensor Data" to begin.</p>
        </div>
      )}
    </div>
  );
}