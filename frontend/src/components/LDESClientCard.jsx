import React, { useEffect, useState,useRef  } from "react";
import { replicateLDES } from "ldes-client";
import { Store } from "n3";
export const data_url_LDES = "https://shehabeldeenayman.github.io/Gent-Terneuzen-canal/LDESTSS/LDESTSS.trig";
export const ldesState = {
  count: 0,
  status: "Initializing...",
  dataLoaded: false,
  store: new Store()
};
export function LDESClientCard() {
  const [status, setStatus] = useState(ldesState.status);
  const [count, setCount] = useState(ldesState.count);
  //const store = useRef(new Store()); // persists across renders

  useEffect(() => {

    if (ldesState.dataLoaded) {
      console.log("Data already loaded, skipping fetch.");
      setStatus("Already Loaded");
      return;
    }
    
      ldesState.store = new Store();
    // We define the async logic INSIDE the effect
    const startStreaming = async () => {
      console.log(`fetching LDES data from ${data_url_LDES}...`);
      setStatus("Fetching...");
      
      try {
        const ldesClient = replicateLDES({
      url: data_url_LDES,
      //fetchOptions: { redirect: "follow" },
      before: new Date("2026-01-01T00:00:00Z"),
      after: new Date("2025-01-01T00:00:00Z"),
    });

        // Get the stream reader
        const reader = ldesClient.stream().getReader();

        let memberCount = 0;
        let result = await reader.read();
        let objects = [];

        while (!result.done) {
          ldesState.count++;
          setCount(ldesState.count); // Update UI with progress
          objects.push(result.value);

          const member = result.value;
          ldesState.store.addQuads(member.quads);

          if (ldesState.count <= 5) {
            console.log(`--- Member ${ldesState.count} ---`, member);
             const triples = member.quads.map((quad) => ({
              subject:   quad.subject.value,
              predicate: quad.predicate.value,
              object:    quad.object.value,
            }));
            console.table(triples); // renders as a nice table in the browser console
          }
          // Process your quads here if needed
          // const quads = result.value.quads;

          result = await reader.read();
        }

        console.log(`Finished streaming. Total members: ${ldesState.count}`);
        //console.log("Processed objects:", objects);


        setStatus("Completed");
      } catch (error) {
        console.error("Error fetching LDES data:", error);
        setStatus("Error: " + error.message);
      }
    };

    
    startStreaming();
    ldesState.dataLoaded = true;
  

  }, []); // The empty array [] ensures this runs only ONCE on mount

  return (
    <div style={{ padding: "20px", border: "1px solid #ccc" }}>
      <h3>LDES Sync Status</h3>
      <p>Status: <strong>{status}</strong></p>
      <p>Members Processed: <strong>{count}</strong></p>
    </div>
  );
}