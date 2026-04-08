export const BodyCard = ({ Top, Bottom }) => (
  <div style={{ 
    display: 'flex', 
    flexDirection: 'column', 
    height: '100%', 
    backgroundColor: '#f9f9f9', 
    padding: '20px', 
    borderRadius: '1em',
    boxSizing: 'border-box',
    overflow: 'hidden' // Prevents the whole card from growing/scrolling
  }}>
    <div style={{ flex: '0 0 auto', marginBottom: '10px' }}> 
      <Top />
    </div>
    
    <div style={{ 
      flex: '1 1 auto', // Takes up all remaining space
      overflowY: 'auto', // This makes ONLY the chart area scrollable
      borderRadius: '1em'
    }}> 
      <Bottom />
    </div>
  </div>
);