import React, { useState ,useEffect} from 'react';
import { BodyCard } from './components/BodyCard';
import { MapCardHead, MapCardBody } from './components/MapCard';
import { BenchmarksCardHead, BenchmarksCardBody } from './components/BenchmarksCard';
import { ChartCardHead,ChartCardBody } from './components/ChartCard';
import { LDESChart } from './components/ChartComponents/LDESChart';
import { LDESTSSChart } from './components/ChartComponents/LDESTSSChart';
import { TTLChart } from './components/ChartComponents/TTLChart';
import { SQLChart } from './components/ChartComponents/SQLChart';
import { QueryCard } from './components/QueryCard';
import { BrowseDataHead,BrowseDataBody } from './components/BrowseData';
import { LDESClientCard } from './components/LDESClientCard';
import { base_url } from './constants';


const App = () => {
  // 1. Initialize state to track the active section
  const [activeTab, setActiveTab] = useState('Station Info');

  const navItems = ['Station Info','Browse Data', 'LDES Client', 'LDES', 'LDES + TSS', 'TTL','SQL', 'Benchmarks', 'Query'];



  const styles = {
    container: { display: 'flex', flexDirection: 'column', height: '100vh', margin: 0, fontFamily: "'Inter', sans-serif" },
    mainContent: { display: 'flex', flex: '0 0 90%', width: '100%' },
    navbar: { 
      flex: '0 0 25%', 
      backgroundColor: '#002353', 
      color: 'white', 
      padding: '2rem 1rem', 
      display: 'flex', 
      flexDirection: 'column', 
      gap: '1rem', 
      boxSizing: 'border-box' 
    },
    body: { 
      flexGrow: 1, 
      backgroundColor: '#FFFFFF', 
      padding: '2rem', 
      overflow: 'hidden', // The scroll happens inside BodyCard now
      height: '100vh',
      boxSizing: 'border-box'
    },
    footer: { 
      flex: '0 0 10%', 
      backgroundColor: '#2C3E50', 
      color: '#BDC3C7', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center' 
    },
    navItem: (isActive) => ({
      fontSize: '1.1rem',
      fontWeight: '500',
      cursor: 'pointer',
      padding: '12px',
      borderRadius: '4px',
      transition: 'all 0.2s',
      listStyle: 'none',
      // Visual feedback: Highlight the active button
      backgroundColor: isActive ? 'rgba(255,255,255,0.2)' : 'transparent',
      borderLeft: isActive ? '4px solid #3498db' : '4px solid transparent',
    }),
  };

const renderBodyContent = () => {
    switch (activeTab) {
      case 'Station Info':
        return (
          <BodyCard Top={MapCardHead} Bottom={MapCardBody} />
  );
      case 'Benchmarks':
        return <BodyCard Top={BenchmarksCardHead} Bottom={() => (<ChartCardBody 
                charts={[
                <BenchmarksCardBody url={`${base_url}ingestbenchmarks`} title="Ingest Benchmarks" />,
                <BenchmarksCardBody url={`${base_url}recallbenchmarks`} title="Recall Benchmarks" />,
                // <BenchmarksCardBody url={`${base_url}objectcountbenchmarks`} title="Object Count Benchmarks" />


              ]} // place multiple charts here
                placeholder="Awaiting Benchmarks..." 
              />)} />
      case 'LDES':
        return (
          <BodyCard 
            Top={() => <ChartCardHead title="LDES Charts" />} 
            Bottom={() => (
              <ChartCardBody 
                charts={[
                <LDESChart 
                URL={`${base_url}virtuoso/ldes/RiverStage1Year`}
                title="River Stage - Virtuoso"
                />,
                  <LDESChart
                URL={`${base_url}virtuoso/ldes/RiverDischarge1Year`}
                title="River Discharge - Virtuoso"
                />,
                <LDESChart
                URL={`${base_url}oxigraph/ldes/RiverStage1Year`}
                title="River Stage - Oxigraph"
                />,
                <LDESChart
                URL={`${base_url}oxigraph/ldes/RiverDischarge1Year`}
                title="River Discharge - Oxigraph"
                />,
              ]} // place multiple charts here
                placeholder="Awaiting Real-Time Streamflow Data for Mol Sluis..." 
              />
            )} 
          />
        );
      case 'LDES + TSS':
        return (
          <BodyCard 
            Top={() => <ChartCardHead title="LDES Charts" />} 
            Bottom={() => (
              <ChartCardBody 
                charts={[
                <LDESTSSChart 
                URL={`${base_url}virtuoso/ldestss/RiverStage1Year`}
                title="River Stage - Virtuoso"
                />,
                <LDESTSSChart 
                URL={`${base_url}virtuoso/ldestss/RiverDischarge1Year`}
                title="River Discharge - Virtuoso"
                />,
                <LDESTSSChart 
                URL={`${base_url}oxigraph/ldestss/RiverStage1Year`}
                title="River Stage - Oxigraph"
                />,
                <LDESTSSChart 
                URL={`${base_url}oxigraph/ldestss/RiverDischarge1Year`}
                title="River Discharge - Oxigraph"
                />,
              ]} // place multiple charts here
                placeholder="Awaiting Real-Time Streamflow Data for Mol Sluis..." 
              />
            )} 
          />
        );
      case 'TTL':
                return (
          <BodyCard 
            Top={() => <ChartCardHead title="LDES Charts" />} 
            Bottom={() => (
              <ChartCardBody 
                charts={[
                <TTLChart 
                URL={`${base_url}virtuoso/ttl/RiverStage1Year`}
                title="River Stage - Virtuoso"
                />,
                                <TTLChart 
                URL={`${base_url}virtuoso/ttl/RiverDischarge1Year`}
                title="River Discharge - Virtuoso"
                />,
                                <TTLChart 
                URL={`${base_url}oxigraph/ttl/RiverStage1Year`}
                title="River Stage - Oxigraph"
                />,
                                <TTLChart 
                URL={`${base_url}oxigraph/ttl/RiverDischarge1Year`}
                title="River Discharge - Oxigraph"
                />,

              ]} // place multiple charts here
                placeholder="Awaiting Real-Time Streamflow Data for Mol Sluis..." 
              />
            )} 
          />
        );
      case 'SQL':
          return (
          <BodyCard 
            Top={() => <ChartCardHead title="LDES Charts" />} 
            Bottom={() => (
              <ChartCardBody 
                charts={[
                  <SQLChart
                    URL={`${base_url}postgres/RiverStage1Year`}
                    title="River Stage - SQL/Postgres"
                  />,
                    <SQLChart
                    URL={`${base_url}postgres/RiverDischarge1Year`}
                    title="River Discharge - SQL/Postgres"
                  />,

              ]} // place multiple charts here
                placeholder="Awaiting Real-Time Streamflow Data for Mol Sluis..." 
              />
            )} 
          />
        );

      case 'Query':
        return(
          <BodyCard
          Top={() => <ChartCardHead title="Query Form"/>}
          Bottom={() =>(
             <QueryCard/>
          )} />
        );

      case 'Browse Data':
        return (<BodyCard
          Top={BrowseDataHead}
          Bottom={BrowseDataBody} />);
        
            case 'LDES Client':
        return (

          <BodyCard
          Top={() => <ChartCardHead title="LDES Client Test"/>}
          Bottom={LDESClientCard} />
        );

      default:
        return <div>Coming Soon...</div>;
    }
  };


  return (
    <div style={styles.container}>
      <div style={styles.mainContent}>
        <nav style={styles.navbar}>
          <h2 style={{ marginBottom: '1.5rem', borderBottom: '1px solid rgba(255,255,255,0.2)', paddingBottom: '1rem' }}>
            Database Central
          </h2>
          <ul style={{ padding: 0, margin: 0 }}>
            {navItems.map((item) => (
              <li 
                key={item} 
                // 3. Update state on click
                onClick={() => setActiveTab(item)}
                style={styles.navItem(activeTab === item)} 
                onMouseOver={(e) => { if(activeTab !== item) e.target.style.background = 'rgba(255,255,255,0.1)' }} 
                onMouseOut={(e) => { if(activeTab !== item) e.target.style.background = 'transparent' }}
              >
                {item}
              </li>
            ))}
          </ul>
        </nav>

        <main style={styles.body}>
{renderBodyContent()}
        </main>
      </div>

      <footer style={styles.footer}>
        <div style={{ textAlign: 'center' }}>
          <p>&copy; 2026 Database Insights. Viewing: <strong>{activeTab}</strong></p>
        </div>
      </footer>
    </div>
  );
};

export default App;