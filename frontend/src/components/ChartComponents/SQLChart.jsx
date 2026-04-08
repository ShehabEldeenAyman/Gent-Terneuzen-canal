import React, { useState, useEffect } from 'react';
import ReactECharts from 'echarts-for-react';

export const SQLChart = ({ URL, title }) => {
  const [data, setData] = useState([]);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hasMore, setHasMore] = useState(true);
  const limit = 100;

  const fetchData = async (targetPage) => {
    setLoading(true);
    try {
      // Fetching from the SQL route with pagination
      const response = await fetch(`${URL}?page=${targetPage}&limit=${limit}`);
      if (!response.ok) throw new Error('Network response was not ok');
      
      const json = await response.json();
      
      // ADJUSTMENT FOR SQL STRUCTURE: 
      // The observations are inside the 'data' array based on your JSON sample
      const newPoints = json.data || [];

      if (newPoints.length < limit) {
        setHasMore(false);
      }

      setData(prevData => {
        const combined = [...prevData, ...newPoints];
        // Sort by time to ensure a continuous line across pages
        return combined.sort((a, b) => new Date(a.time) - new Date(b.time));
      });
      
      setError(null);
    } catch (err) {
      setError(`Failed to load SQL data: ${err.message}`);
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
      text: title || 'River Monitoring (SQL/Postgres)',
      left: 'center',
      textStyle: { fontSize: 16, color: '#333' }
    },
    tooltip: { 
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    grid: { bottom: '15%', containLabel: true },
    dataZoom: [
      { type: 'slider', start: 0, end: 100 },
      { type: 'inside' }
    ],
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: data.map(item => new Date(item.time).toLocaleString()),
    },
    yAxis: {
      type: 'value',
      scale: true,
      name: 'Stage (m)'
    },
    series: [
      {
        name: 'SQL Observation',
        type: 'line',
        symbol: 'none',
        sampling: 'lttb',
        large: true,
        itemStyle: { color: '#8e44ad' }, // Purple for SQL to differentiate from LDES/TTL
        areaStyle: {
            color: {
              type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(142, 68, 173, 0.3)' },
                { offset: 1, color: 'rgba(142, 68, 173, 0)' }
              ]
            }
        },
        // Mapping 'val' property from your SQL JSON structure
        data: data.map(item => parseFloat(item.val))
      }
    ]
  });

  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', background: '#fff', padding: '10px', borderRadius: '8px', boxSizing: 'border-box' }}>
      {error && <div style={{ color: 'red', marginBottom: '10px' }}>{error}</div>}
      
      <div style={{ flexGrow: 1, minHeight: '350px' }}>
        <ReactECharts 
          option={getOption()} 
          style={{ height: '100%', width: '100%' }} 
          notMerge={true} 
        />
      </div>

      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '15px', marginTop: '10px' }}>
        <span style={{ fontSize: '0.9rem', color: '#666' }}>Records: <strong>{data.length}</strong></span>
        <button 
          onClick={loadMore} 
          disabled={loading || !hasMore}
          style={{
            ...buttonStyle,
            opacity: (loading || !hasMore) ? 0.5 : 1,
            cursor: (loading || !hasMore) ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? 'Querying...' : hasMore ? 'Load Next 100 Rows' : 'End of Database'}
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
  backgroundColor: '#8e44ad',
  color: 'white',
  border: 'none',
  borderRadius: '4px',
  fontWeight: '600'
};

