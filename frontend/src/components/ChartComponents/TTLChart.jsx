import React, { useState, useEffect } from 'react';
import ReactECharts from 'echarts-for-react';

export const TTLChart = ({ URL, title }) => {
  const [data, setData] = useState([]);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hasMore, setHasMore] = useState(true);
  const limit = 100; // Standard limit for flat observation arrays

  const fetchData = async (targetPage) => {
    setLoading(true);
    try {
      const response = await fetch(`${URL}?page=${targetPage}&limit=${limit}`);
      if (!response.ok) throw new Error('Network response was not ok');
      
      const json = await response.json();
      
      // If we receive fewer items than the limit, we've reached the end
      if (json.length < limit) {
        setHasMore(false);
      }

      setData(prevData => {
        // TTL data can sometimes have duplicate timestamps if multiple sensors 
        // or versions are present. We merge and then sort by time.
        const combined = [...prevData, ...json];
        
        // Sorting is crucial for TTL data to ensure the ECharts line connects correctly
        return combined.sort((a, b) => new Date(a.time) - new Date(b.time));
      });
      
      setError(null);
    } catch (err) {
      setError(`Failed to load TTL data: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData(1);
  }, []);

  const loadMore = () => {
    const nextPage = page + 1;
    setPage(nextPage);
    fetchData(nextPage);
  };

  const getOption = () => ({
    title: {
      text: title || 'River Monitoring (TTL)',
      left: 'center',
      textStyle: { fontSize: 16, color: '#333' }
    },
    tooltip: { 
      trigger: 'axis',
      formatter: (params) => {
        const item = params[0];
        // Formatting to 3 decimal places for clarity with TTL high-precision floats
        return `${item.name}<br/>Value: <b>${parseFloat(item.value).toFixed(3)}</b>`;
      }
    },
    toolbox: {
      feature: {
        dataZoom: { yAxisIndex: 'none' },
        restore: {},
        saveAsImage: {}
      }
    },
    dataZoom: [
      { type: 'slider', start: 0, end: 100 },
      { type: 'inside' }
    ],
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: data.map(item => new Date(item.time).toLocaleString()),
      axisLabel: { fontSize: 10 }
    },
    yAxis: {
      type: 'value',
      scale: true, // Focus on the specific range (e.g., 29.6m to 29.8m)
      name: 'Stage (m)',
      splitLine: { show: true, lineStyle: { type: 'dashed' } }
    },
    series: [
      {
        name: 'Observation',
        type: 'line',
        symbol: 'none',
        sampling: 'lttb', // Optimization for large datasets
        large: true,
        itemStyle: { color: '#27ae60' }, // Green color for TTL data distinction
        areaStyle: {
          color: {
            type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(39, 174, 96, 0.3)' },
              { offset: 1, color: 'rgba(39, 174, 96, 0)' }
            ]
          }
        },
        data: data.map(item => parseFloat(item.value))
      }
    ]
  });

  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', background: '#fff', padding: '10px', borderRadius: '8px', boxSizing: 'border-box' }}>
      {error && <div style={{ color: '#721c24', backgroundColor: '#f8d7da', padding: '10px', borderRadius: '4px' }}>{error}</div>}
      
      <div style={{ flexGrow: 1, minHeight: '350px' }}>
        <ReactECharts 
          option={getOption()} 
          style={{ height: '100%', width: '100%' }} 
          notMerge={true} 
        />
      </div>

      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '15px', marginTop: '10px' }}>
        <div style={{ fontSize: '0.9rem', color: '#666' }}>
            Loaded: <strong>{data.length}</strong> points
        </div>
        <button 
          onClick={loadMore} 
          disabled={loading || !hasMore}
          style={{
            ...buttonStyle,
            opacity: (loading || !hasMore) ? 0.5 : 1,
            cursor: (loading || !hasMore) ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? 'Fetching...' : hasMore ? 'Load More Data' : 'All Data Loaded'}
        </button>
        <button 
          onClick={() => { setData([]); setPage(1); setHasMore(true); fetchData(1); }}
          style={{ ...buttonStyle, backgroundColor: '#6c757d' }}
        >
          Reset
        </button>
      </div>
    </div>
  );
};

const buttonStyle = {
  padding: '8px 16px',
  backgroundColor: '#27ae60',
  color: 'white',
  border: 'none',
  borderRadius: '4px',
  fontWeight: '600'
};

