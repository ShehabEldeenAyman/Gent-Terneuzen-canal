import React, { useEffect, useRef, useState } from "react";
import { replicateLDES } from "ldes-client";

export const data_url_LDES =
  "https://shehabeldeenayman.github.io/Gent-Terneuzen-canal/LDESTSS/LDESTSS.trig";

export function LDESClientCard() {
  const [status, setStatus] = useState("Initializing...");
  const [count, setCount] = useState(0);

  /**
   * members: Array of LDES member objects.
   * Each entry has the shape:
   *   {
   *     id:    string,           // member IRI (or auto-generated index)
   *     quads: Quad[],           // the raw RDF quads belonging to this member
   *   }
   *
   * Quads follow the RDF/JS data model:
   *   quad.subject   – NamedNode | BlankNode
   *   quad.predicate – NamedNode
   *   quad.object    – NamedNode | BlankNode | Literal
   *   quad.graph     – NamedNode | DefaultGraph
   */
  const [members, setMembers] = useState([]);

  // Keep a mutable ref so the streaming loop always appends to the latest list
  // without needing `members` in the useEffect dependency array.
  const membersRef = useRef([]);

  // Abort controller so cleanup can cancel the reader on unmount.
  const readerRef = useRef(null);

  useEffect(() => {
    const startStreaming = async () => {
      console.log(`Fetching LDES data from ${data_url_LDES}…`);
      setStatus("Fetching…");

      try {
        const ldesClient = replicateLDES({
          url: data_url_LDES,
          fetchOptions: { redirect: "follow" },
        });

        const reader = ldesClient.stream().getReader();
        readerRef.current = reader;

        let memberIndex = 0;
        let result = await reader.read();

        while (!result.done) {
          const raw = result.value;

          /**
           * Build a serialisable member object.
           *
           * `raw` is an LDES Member. Depending on the ldes-client version it
           * exposes its quads either via:
           *   • raw.quads          – an array of RDF/JS Quad objects, OR
           *   • raw.dataset        – an N3.js DatasetCore / Store
           *
           * We normalise both cases into a plain array of quad objects so the
           * rest of the app has a single, predictable shape to work with.
           */
          let quads = [];

          if (Array.isArray(raw?.quads)) {
            quads = raw.quads;
          } else if (raw?.dataset) {
            // DatasetCore / N3.Store: spread the iterable
            quads = [...raw.dataset];
          } else if (raw?.[Symbol.iterator]) {
            // Fallback: member itself may be an iterable of quads
            quads = [...raw];
          }

          const member = {
            // Use the member's subject IRI when available, otherwise index
            id: raw?.id?.value ?? raw?.subject?.value ?? `member-${memberIndex}`,
            quads,
          };

          // Append to the ref and update state in one batch
          membersRef.current = [...membersRef.current, member];
          memberIndex++;

          setCount(memberIndex);
          // Spread so React sees a new array reference and re-renders
          setMembers([...membersRef.current]);

          result = await reader.read();
        }

        setStatus(`Completed — ${memberIndex} member(s) loaded`);
      } catch (error) {
        if (error.name !== "AbortError") {
          console.error("Error fetching LDES data:", error);
          setStatus("Error: " + error.message);
        }
      }
    };

    startStreaming();

    // Cleanup: cancel the stream reader if the component unmounts mid-stream
    return () => {
      readerRef.current?.cancel?.();
    };
  }, []);

  /* ------------------------------------------------------------------ */
  /* Helpers for rendering quads                                          */
  /* ------------------------------------------------------------------ */

  /** Shorten a long IRI to a readable prefix:localName form */
  const shorten = (term) => {
    if (!term) return "—";
    const v = term.value ?? String(term);
    // Grab everything after the last # or /
    const local = v.split(/[#/]/).pop();
    return local && local !== v ? `…/${local}` : v;
  };

  const termLabel = (term) => {
    if (!term) return "—";
    if (term.termType === "Literal") return `"${term.value}"`;
    return shorten(term);
  };

  /* ------------------------------------------------------------------ */
  /* Render                                                               */
  /* ------------------------------------------------------------------ */

  return (
    <div style={styles.card}>
      {/* Header */}
      <div style={styles.header}>
        <h3 style={styles.title}>LDES Sync Status</h3>
        <span style={styles.badge}>{status}</span>
      </div>

      <p style={styles.counter}>
        Members stored: <strong>{count}</strong>
      </p>

      {/* Member list */}
      
 

 

      
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Styles                                                               */
/* ------------------------------------------------------------------ */

const styles = {
  card: {
    fontFamily: "'Segoe UI', sans-serif",
    padding: "20px",
    border: "1px solid #ccc",
    borderRadius: "8px",
    maxWidth: "900px",
    background: "#fafafa",
  },
  header: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    marginBottom: "8px",
  },
  title: {
    margin: 0,
    fontSize: "1.1rem",
  },
  badge: {
    fontSize: "0.78rem",
    padding: "2px 10px",
    borderRadius: "999px",
    background: "#e8f4ff",
    color: "#0066cc",
    border: "1px solid #b3d4f5",
  },
  counter: {
    margin: "4px 0 16px",
    color: "#444",
    fontSize: "0.9rem",
  },
  memberList: {
    display: "flex",
    flexDirection: "column",
    gap: "8px",
  },
  memberDetails: {
    border: "1px solid #ddd",
    borderRadius: "6px",
    overflow: "hidden",
    background: "#fff",
  },
  memberSummary: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    padding: "8px 12px",
    cursor: "pointer",
    background: "#f0f4f8",
    userSelect: "none",
    fontSize: "0.85rem",
  },
  memberIndex: {
    fontWeight: "bold",
    color: "#888",
    minWidth: "32px",
  },
  memberId: {
    flex: 1,
    fontFamily: "monospace",
    fontSize: "0.8rem",
    color: "#333",
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  },
  quadCount: {
    color: "#666",
    fontSize: "0.78rem",
    whiteSpace: "nowrap",
  },
  tableWrapper: {
    overflowX: "auto",
  },
  table: {
    width: "100%",
    borderCollapse: "collapse",
    fontSize: "0.78rem",
  },
  th: {
    padding: "6px 10px",
    textAlign: "left",
    background: "#e8edf2",
    fontWeight: "600",
    color: "#555",
    borderBottom: "1px solid #ddd",
    whiteSpace: "nowrap",
  },
  td: {
    padding: "5px 10px",
    fontFamily: "monospace",
    color: "#333",
    maxWidth: "220px",
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
    borderBottom: "1px solid #eee",
  },
  trEven: { background: "#fff" },
  trOdd:  { background: "#f9fafb" },
};
