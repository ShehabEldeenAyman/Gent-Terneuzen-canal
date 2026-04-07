import React, { useEffect, useState } from "react";
import { replicateLDES } from "ldes-client";

export const data_url_LDES = "https://shehabeldeenayman.github.io/Mol_sluis_Dessel_Usecase/LDES/LDES.trig";

export function LDESClientCard() {
  const [status, setStatus] = useState("Initializing...");
  const [count, setCount] = useState(0);

  useEffect(() => {
    // We define the async logic INSIDE the effect
    const startStreaming = async () => {
      console.log(`fetching LDES data from ${data_url_LDES}...`);
      setStatus("Fetching...");
      
      try {
        const ldesClient = replicateLDES({
      url: data_url_LDES,
      fetchOptions: { redirect: "follow" }
    });

        // Get the stream reader
        const reader = ldesClient.stream().getReader();

        let memberCount = 0;
        let result = await reader.read();

        while (!result.done) {
          memberCount++;
          setCount(memberCount); // Update UI with progress
          
          // Process your quads here if needed
          // const quads = result.value.quads;

          result = await reader.read();
        }

        setStatus("Completed");
      } catch (error) {
        console.error("Error fetching LDES data:", error);
        setStatus("Error: " + error.message);
      }
    };

    startStreaming();
  }, []); // The empty array [] ensures this runs only ONCE on mount

  return (
    <div style={{ padding: "20px", border: "1px solid #ccc" }}>
      <h3>LDES Sync Status</h3>
      <p>Status: <strong>{status}</strong></p>
      <p>Members Processed: <strong>{count}</strong></p>
    </div>
  );
}