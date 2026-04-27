import React, { useEffect, useState } from "react";
import { replicateLDES } from "ldes-client";

export const data_url_LDES = "https://shehabeldeenayman.github.io/Gent-Terneuzen-canal/LDESTSS/LDESTSS.trig";

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
      fetchOptions: { redirect: "follow" },
      before: new Date("2026-01-01T00:00:00Z"),
      after: new Date("2025-01-01T00:00:00Z"),
    });

        // Get the stream reader
        const reader = ldesClient.stream().getReader();

        let memberCount = 0;
        let result = await reader.read();
        let objects = [];

        while (!result.done) {
          memberCount++;
          setCount(memberCount); // Update UI with progress
          objects.push(result.value);

          const member = result.value;
          if (member.quads && Array.isArray(member.quads)&&memberCount==1) { // Limit to first 10 members for logging
          member.quads.forEach((quad) => {
            // Accessing the components
            const subject = quad.subject.value;
            const predicate = quad.predicate.value;
            const object = quad.object.value;

            console.log(`S: ${subject} | P: ${predicate} | O: ${object}`);
          });
        }
          // Process your quads here if needed
          // const quads = result.value.quads;

          result = await reader.read();
        }

        console.log(`Finished streaming. Total members: ${memberCount}`);
        //console.log("Processed objects:", objects);


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