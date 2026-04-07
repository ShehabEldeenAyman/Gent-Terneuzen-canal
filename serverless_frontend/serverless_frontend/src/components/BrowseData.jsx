import React, { useState, useEffect } from 'react';
import { base_url } from '../constants';

const innerStyles = {
  container: {
    height: '100%',
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
  },
  navItem: (isActive) => ({
    cursor: 'pointer',
    fontWeight: isActive ? 'bold' : 'normal',
    opacity: isActive ? 1 : 0.7,
    transition: 'opacity 0.2s',
    color: '#000000',
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
    textAlign: 'center',
    fontSize: '1.4rem',
    fontWeight: '700',
    marginBottom: '0',
    marginTop: '0',
  }
};

const tableStyles = {
  controls: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '1rem',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    marginTop: '10px',
    fontSize: '0.85rem',
    backgroundColor: 'white',
  },
  th: {
    borderBottom: '2px solid #ddd',
    padding: '10px',
    textAlign: 'left',
    backgroundColor: '#f2f2f2',
    color: 'black',
    textTransform: 'capitalize'
  },
  td: {
    borderBottom: '1px solid #ddd',
    padding: '8px',
    wordBreak: 'break-all',
    color: '#333'
  },
  button: {
    padding: '5px 15px',
    cursor: 'pointer',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px'
  }
};

export const BrowseDataHead = () => (
  <div>
    <h2 style={headStyles.title}>Browse Data</h2>
  </div>
);

export const BrowseDataBody = () => {
  const [activeSubTab, setActiveSubTab] = useState('LDES');
  const menuItems = ['LDES', 'LDES + TSS', 'TTL'];

  const renderSubContent = () => {
    switch (activeSubTab) {
      case 'LDES': return <BrowseLDESData />;
      case 'LDES + TSS': return <BrowseLDESTSSData />;
      case 'TTL': return <BrowseTTLData />;
      default: return <div><h3>Overview Content Placeholder</h3></div>;
    }
  };

  return (
    <div style={innerStyles.container}>
      <div style={innerStyles.subNavbar}>
        {menuItems.map((item, index) => (
          <React.Fragment key={item}>
            <span 
              style={innerStyles.navItem(activeSubTab === item)}
              onClick={() => setActiveSubTab(item)}
            >
              {item}
            </span>
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

const BrowseTTLData = () => {
  const [data, setData] = useState([]);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  
  // Example SPARQL query
const sparqlQuery = `PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX ex: <http://example.org/>
SELECT ?subject ?value ?time ?runoffvalue ?observedproperty
WHERE {
  ?subject sosa:hasSimpleResult ?value ;
           sosa:resultTime ?time;
           sosa:observedProperty ?observedproperty .
           
  OPTIONAL { 
    ?subject ex:hasRunoff ?runoffvalue 
  }
}
ORDER BY DESC(?time)`;

  const fetchData = async () => {
    setLoading(true);
    try {
      const encodedQuery = encodeURIComponent(sparqlQuery);
      const response = await fetch(`${base_url}virtuoso/ttl/query?page=${page}&query=${encodedQuery}`);
      const result = await response.json();
      setData(Array.isArray(result) ? result : (result.results?.bindings || []));
    } catch (error) {
      console.error("Error fetching TTL data:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [page]);

  // HIGHLIGHTED CHANGE: Determine columns dynamically from the keys of the first data object
  const columns = data.length > 0 ? Object.keys(data[0]) : [];

  return (
    <div>
      <div style={{...tableStyles.controls, justifyContent: 'flex-end'}}>
        <div>
          <button 
            disabled={page === 1 || loading}
            style={{...tableStyles.button, marginRight: '10px', opacity: (page === 1 || loading) ? 0.5 : 1}}
            onClick={() => setPage(prev => Math.max(prev - 1, 1))}
          >
            Previous
          </button>
          <span style={{color: 'black', fontWeight: 'bold'}}>Page {page}</span>
          <button 
            disabled={loading || data.length < 100}
            style={{...tableStyles.button, marginLeft: '10px', opacity: (loading || data.length < 100) ? 0.5 : 1}}
            onClick={() => setPage(prev => prev + 1)}
          >
            Next
          </button>
        </div>
      </div>

      {loading ? (
        <p>Loading data...</p>
      ) : (
        <table style={tableStyles.table}>
          <thead>
            <tr>
              {/* Generate headers dynamically */}
              {columns.map(key => (
                <th key={key} style={tableStyles.th}>{key}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.length > 0 ? (
              data.map((row, rowIndex) => (
                <tr key={rowIndex}>
                  {/* Generate cells dynamically based on the keys */}
                  {columns.map(key => (
                    <td key={`${rowIndex}-${key}`} style={tableStyles.td}>
                      {row[key] !== null && row[key] !== undefined ? row[key].toString() : ''}
                    </td>
                  ))}
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={columns.length || 1} style={{textAlign: 'center', padding: '20px'}}>No data found</td>
              </tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  );
};

const BrowseLDESData = () => (<div><h3>LDES Data Placeholder</h3></div>);
const BrowseLDESTSSData = () => (<div><h3>LDES + TSS Data Placeholder</h3></div>);