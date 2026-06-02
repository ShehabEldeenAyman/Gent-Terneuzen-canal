import React, { useEffect, useState } from "react";
import { replicateLDES } from "ldes-client";
import { Store } from "n3";

// A global registry map to store separate states for each URL
// This ensures data stays cached when you switch tabs
export const ldesRegistry = {};

// Helper function to get or initialize an LDES state for a specific URL
export function getLdesState(url) {
  if (!url) return { count: 0, status: "No URL provided", dataLoaded: false, store: new Store() };
  
  if (!ldesRegistry[url]) {
    ldesRegistry[url] = {
      count: 0,
      status: "Initializing...",
      dataLoaded: false,
      store: new Store()
    };
  }
  return ldesRegistry[url];
}

// 1. Accept 'url' as a parameter (prop)
export function LDESClientCard({ url }) {
  // Grab the specific state bucket belonging to this URL
  const ldesState = getLdesState(url);

  const [status, setStatus] = useState(ldesState.status);
  const [count, setCount] = useState(ldesState.count);
  const [sampleTriples, setSampleTriples] = useState([]);

  useEffect(() => {
    if (!url) return;

    // If this URL has already finished streaming, skip downloading it again
    if (ldesState.dataLoaded) {
      console.log(`Data already loaded for ${url}, skipping fetch.`);
      setStatus("Already Loaded");
      return;
    }
    
    const startStreaming = async () => {
      console.log(`fetching LDES data from ${url}...`);
      setStatus("Fetching...");
      ldesState.status = "Fetching...";
      
      try {
        const ldesClient = replicateLDES({
          url: url,
          before: new Date("2025-12-31T00:00:00Z"),
          after: new Date("2025-01-01T00:00:00Z"),
        });

        const reader = ldesClient.stream().getReader();
        let result = await reader.read();

        while (!result.done) {
          ldesState.count++;
          setCount(ldesState.count); // Update UI progress

          const member = result.value;
          // Add data directly to this URL's specific store
          ldesState.store.addQuads(member.quads);

          if (ldesState.count <= 5) {
            const triples = member.quads.map((quad) => ({
              subject:   quad.subject.value,
              predicate: quad.predicate.value,
              object:    quad.object.value,
            }));
            setSampleTriples(prev => [...prev, ...triples]);
          }

          result = await reader.read();
        }

        console.log(`Finished streaming ${url}. Total members: ${ldesState.count}`);
        setStatus("Completed");
        ldesState.status = "Completed";
        ldesState.dataLoaded = true;
      } catch (error) {
        console.error(`Error fetching LDES data from ${url}:`, error);
        setStatus("Error: " + error.message);
        ldesState.status = "Error: " + error.message;
      }
    };

    startStreaming();

  }, [url]); // If the URL parameter changes, re-run this effect

  return (
    <div>
      <div style={{ padding: "20px", border: "1px solid #ccc", borderRadius: "8px" }}>
        <h3>LDES Sync Status</h3>
        <p style={{ wordBreak: 'break-all' }}>URL: <code style={{ background: '#f4f4f4', padding: '2px 4px' }}>{url}</code></p>
        <p>Status: <strong>{status}</strong></p>
        <p>Members Processed: <strong>{count}</strong></p>
      </div>
      <pre style={{ fontSize: '11px', overflow: 'auto', maxHeight: '300px', marginTop: '10px', background: '#fafafa', padding: '10px' }}>
        {JSON.stringify(sampleTriples, null, 2)}
      </pre>
    </div>
  );
}