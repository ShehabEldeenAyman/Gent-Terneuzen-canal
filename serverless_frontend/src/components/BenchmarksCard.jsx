import React, { useState,useEffect } from 'react';
import ReactECharts from 'echarts-for-react';

export const BenchmarksCardHead = () => {
    return (
        <div >
            <h2 style={{ fontSize: '1.5rem', color: '#333' }}>Benchmarks</h2>
        </div>
    );
}

export const BenchmarksCardBody = ({url,title}) => {
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Fetch data from the local benchmarks endpoint
    fetch(url)
      .then((response) => {
        if (!response.ok) {
          throw new Error("Network response was not ok");
        }
        return response.json();
      })
      .then((data) => {
        setChartData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching benchmarks:", err);
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const getOption = () => {
    if (!chartData) return {};

    // Map the object keys to readable labels and values to numbers
    const labels = Object.keys(chartData).map(key => 
      key.replace(/_/g, ' ').toUpperCase()
    );
    const values = Object.values(chartData);

    return {
      title: {
        text: `${title}`,
        left: 'center',
        textStyle: { fontSize: 14 }
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: labels,
        axisLabel: {
          rotate: 30,
          interval: 0,
          fontSize: 10
        }
      },
      yAxis: {
        type: 'value',
        name: 'Time (s)',
      },
      series: [
        {
          name: 'Execution Time',
          type: 'bar',
          data: values,
          itemStyle: {
            color: '#1523e0' // Matching your app's primary blue
          },
          label: {
            show: true,
            position: 'top',
            formatter: '{c}'
          }
        }
      ]
    };
  };

  if (loading) return <div>Loading benchmarks...</div>;
  if (error) return <div>Error loading data: {error}</div>;

  return (
    <div style={{ height: '100%', width: '100%', padding: '10px' }}>
      <ReactECharts 
        option={getOption()} 
        style={{ height: '400px', width: '100%' }} 
      />
    </div>
  );
};