import React, { useState, useEffect } from "react";
import ReactECharts from "echarts-for-react";
import { DataFactory } from "n3";
// Import our new helper function instead of the static ldesState object
import { getLdesState } from "./LDESClientCard";

const { namedNode } = DataFactory;

const PREFIXES = {
  TSS: "https://w3id.org/tss#",
  RDF: "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
};

// URL-keyed registry — mirrors the ldesRegistry pattern in LDESClientCard.
// Each URL gets its own cache so conductivity and precipitation never overwrite each other.
const sensorDataRegistry = {};

export function getSensorDataCache(url) {
  if (!sensorDataRegistry[url]) {
    sensorDataRegistry[url] = { sensorDataMap: {}, activeSensors: [] };
  }
  return sensorDataRegistry[url];
}

// Accept both the target IDs AND the URL we want to visualize
export function DataVisualization({ targetSensorIds, ldesUrl }) {
  const cache = getSensorDataCache(ldesUrl);
  const [sensorDataMap, setSensorDataMap] = useState(cache.sensorDataMap);
  const [activeSensors, setActiveSensors] = useState(cache.activeSensors);

  // Dynamically get the state associated with the passed URL
  const ldesState = getLdesState(ldesUrl);

  useEffect(() => {
    const c = getSensorDataCache(ldesUrl);
    c.sensorDataMap = sensorDataMap;
    c.activeSensors = activeSensors;
  }, [sensorDataMap, activeSensors, ldesUrl]);

  const handleLoadData = () => {
    // Read directly from the dynamic URL store instance
    if (!ldesState || ldesState.count === 0) {
      alert("No data available yet! Please fetch data via the LDES Client tab first.");
      return;
    }

    const snippetSubjects = ldesState.store
      .getQuads(null, namedNode(PREFIXES.RDF + "type"), namedNode(PREFIXES.TSS + "Snippet"), null)
      .map(q => q.subject.value);

    const tempMap = {};
    const foundSensors = new Set();

    snippetSubjects.forEach(uri => {
      const uriParts = uri.split('/');
      const waterInfoIndex = uriParts.indexOf('waterinfo');
      const extractedId = uriParts[waterInfoIndex + 1];

      if (targetSensorIds.includes(extractedId)) {
        foundSensors.add(extractedId);

        const pointsRecord = ldesState.store.getQuads(
          namedNode(uri), 
          namedNode(PREFIXES.TSS + "points"), 
          null, 
          null
        )[0];

        const rawPoints = pointsRecord?.object.value;
        
        if (rawPoints) {
          const parsedPoints = JSON.parse(rawPoints);
          const formattedPoints = parsedPoints.map(p => [p.time, p.value]);

          if (!tempMap[extractedId]) {
            tempMap[extractedId] = [];
          }
          tempMap[extractedId].push(...formattedPoints);
        }
      }
    });

    Object.keys(tempMap).forEach(id => {
      tempMap[id].sort((a, b) => new Date(a[0]) - new Date(b[0]));
    });

    setSensorDataMap(tempMap);
    setActiveSensors(Array.from(foundSensors));
  };

  const getOption = () => {
    const series = activeSensors.map(id => ({
      name: `Sensor ${id}`,
      type: 'line',
      data: sensorDataMap[id],
      showSymbol: false,
      smooth: true,
      lineStyle: { width: 2 }
    }));

    return {
      title: { text: 'Conductivity Measurements by Sensor', left: 'center', top: 10 },
      tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
      legend: { data: activeSensors.map(id => `Sensor ${id}`), bottom: 50 },
      grid: { left: '5%', right: '5%', bottom: '22%', containLabel: true },
      xAxis: { type: 'time', name: 'Date', nameLocation: 'middle', nameGap: 35 },
      yAxis: { type: 'value', name: 'μS/cm', nameLocation: 'middle', nameGap: 50 },
      dataZoom: [{ type: 'slider', xAxisIndex: 0, filterMode: 'filter' }, { type: 'inside', xAxisIndex: 0 }],
      series: series
    };
  };

  return (
    <div style={{ padding: "20px", border: "1px solid #ddd", borderRadius: "12px", background: "#fff" }}>
      <div style={{ marginBottom: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <button 
          onClick={handleLoadData} 
          style={{ padding: '10px 20px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '5px', cursor: 'pointer' }}
        >
          Load Sensor Data
        </button>
        <span style={{ fontSize: '14px', color: '#666' }}>
          Sensors Found: {activeSensors.length} / {targetSensorIds.length}
        </span>
      </div>

      {activeSensors.length > 0 ? (
        <ReactECharts option={getOption()} style={{ height: '550px', width: '100%' }} notMerge={true} />
      ) : (
        <div style={{ height: '550px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: '#fcfcfc', border: '1px dashed #ccc', borderRadius: '8px' }}>
          <p style={{ color: '#888' }}>Ready to load. Click "Load Sensor Data" to begin visualizing.</p>
        </div>
      )}
    </div>
  );
}