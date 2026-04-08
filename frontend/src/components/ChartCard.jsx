import React, { useState, useEffect } from 'react';
import ReactECharts from 'echarts-for-react';

export const ChartCardHead = ({title}) => {
    return (
        <div>
            <   h2 style={{ fontSize: '1.5rem', color: '#333' }}>{title}</h2>
        </div>
    );
}

// ChartCard.jsx

export const ChartCardBody = ({ charts = [], placeholder = "No charts available" }) => {
    const gridStyles = {
        container: {
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: '1.5rem',
            width: '100%',
            boxSizing: 'border-box',
            padding: '0.5rem'
        },
        chartItem: {
            backgroundColor: '#ffffff', // Solid background so they look like distinct cards
            borderRadius: '12px',
            border: '1px solid #e0e0e0',
            display: 'flex',
            flexDirection: 'column',
            padding: '1rem',
            boxSizing: 'border-box',
            minHeight: '450px', // Ensures buttons have enough room to exist
            boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
        }
    };

    if (charts.length === 0) {
        return (
            <div style={gridStyles.container}>
                <div style={{ ...gridStyles.chartItem, gridColumn: 'span 2', minHeight: '200px' }}>
                    <p style={{ fontStyle: 'italic' }}>{placeholder}</p>
                </div>
            </div>
        );
    }

    return (
        <div style={gridStyles.container}>
            {charts.map((chart, index) => (
                <div key={index} style={gridStyles.chartItem}>
                    {chart}
                </div>
            ))}
        </div>
    );
};