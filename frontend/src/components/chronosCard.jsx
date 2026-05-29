import React, { useState } from "react";

// ─────────────────────────────────────────────────────────────────────────────
// Configuration: define your grid items here.
// Each entry needs:
//   id         – unique key
//   label      – figure caption shown below the image
//   apiUrl     – the endpoint that returns a PNG (GET request)
// ─────────────────────────────────────────────────────────────────────────────
const backendBase = "http://127.0.0.1:8000";
const GRAPH_ITEMS = [
  {
    id: "Chronos-2_Forecast",
    label: "Chronos-2 Forecast",
    apiUrl: `${backendBase}/chronos2forecast`,
  }
];

// ─────────────────────────────────────────────────────────────────────────────
// GraphCard – a single cell in the grid
// ─────────────────────────────────────────────────────────────────────────────
function GraphCard({ item }) {
  // status: "idle" | "loading" | "loaded" | "error"
  const [status, setStatus] = useState("idle");
  const [imgSrc, setImgSrc] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");

  const handleLoad = async () => {
    setStatus("loading");
    setImgSrc(null);
    setErrorMsg("");

    try {
      const response = await fetch(item.apiUrl);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const blob = await response.blob();
      const objectUrl = URL.createObjectURL(blob);
      setImgSrc(objectUrl);
      setStatus("loaded");
    } catch (err) {
      setErrorMsg(err.message || "Failed to load graph.");
      setStatus("error");
    }
  };

  return (
  
<figure style={styles.card}>
      {/* ── Preview area ── */}
      <div style={styles.imageArea}>
        {status === "idle" && (
          <div style={styles.placeholder}>
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#aab" strokeWidth="1.5">
              <rect x="3" y="3" width="18" height="18" rx="2" />
              <path d="M3 9l4-4 4 4 4-6 4 6" />
              <circle cx="8.5" cy="13.5" r="1.5" />
            </svg>
            <p style={styles.placeholderText}>No data loaded</p>
          </div>
        )}

        {status === "loading" && (
          <div style={styles.placeholder}>
            <div style={styles.spinner} />
            <p style={styles.placeholderText}>Fetching graph…</p>
          </div>
        )}

        {status === "loaded" && (
          <img
            src={imgSrc}
            alt={item.label}
            style={styles.image}
          />
        )}

        {status === "error" && (
          <div style={{ ...styles.placeholder, gap: "8px" }}>
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#e05" strokeWidth="1.5">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 8v4M12 16h.01" />
            </svg>
            <p style={{ ...styles.placeholderText, color: "#e05" }}>Error: {errorMsg}</p>
          </div>
        )}
      </div>

      {/* ── Load button ── */}
      <button
        onClick={handleLoad}
        disabled={status === "loading"}
        style={{
          ...styles.button,
          ...(status === "loading" ? styles.buttonDisabled : {}),
          ...(status === "loaded" ? styles.buttonLoaded : {}),
        }}
      >
        {status === "loading"
          ? "Loading…"
          : status === "loaded"
          ? "↺ Reload"
          : "Load Graph"}
      </button>

      {/* ── Caption ── */}
      <figcaption style={styles.caption}>{item.label}</figcaption>
    </figure>

    
 
    
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// GraphGrid – the main exported component
// ─────────────────────────────────────────────────────────────────────────────
export function chronosCard({ items = GRAPH_ITEMS }) {
  const [loadingAll, setLoadingAll] = useState(false);

  // Ref trick: trigger all cards via their own handlers isn't ideal in this
  // pattern, so we expose a "load all" by re-mounting (key trick) or simply
  // let each card manage itself. Here we provide a global "Load All" that
  // fires the individual card loads via a shared trigger counter.
  const [globalTrigger, setGlobalTrigger] = useState(0);

  return (
    <div style={styles.wrapper}>
      {/* ── Header bar ── */}
      {/* <div style={styles.header}>
        <h3 style={styles.heading}>Graph Overview</h3>
        <span style={styles.subheading}>{items.length} charts</span>
      </div> */}

      {/* ── Grid ── */}
      <div>
        {items.map((item) => (
          <GraphCard key={item.id} item={item} />
        ))}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Styles
// ─────────────────────────────────────────────────────────────────────────────
const styles = {
  wrapper: {
    padding: "10px",
    fontFamily: "'IBM Plex Sans', 'Segoe UI', sans-serif",
  },

  header: {
    display: "flex",
    alignItems: "baseline",
    gap: "12px",
    marginBottom: "20px",
    borderBottom: "2px solid #002353",
    paddingBottom: "10px",
  },

  heading: {
    margin: 0,
    fontSize: "1.3rem",
    fontWeight: 700,
    color: "#002353",
    letterSpacing: "-0.02em",
  },

  subheading: {
    fontSize: "0.85rem",
    color: "#888",
    fontWeight: 400,
  },

  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
    gap: "20px",
  },

  // ── Card ──
  card: {
    margin: 0,
    display: "flex",
    flexDirection: "column",
    border: "1px solid #e0e4ea",
    borderRadius: "10px",
    overflow: "hidden",
    background: "#fff",
    boxShadow: "0 1px 4px rgba(0,0,0,0.07)",
    transition: "box-shadow 0.2s",
  },

  // ── Image area ──
  imageArea: {
    width: "100%",
    aspectRatio: "16 / 9",
    backgroundColor: "#f5f7fa",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    overflow: "hidden",
    borderBottom: "1px solid #e0e4ea",
  },

  image: {
    width: "100%",
    height: "100%",
    objectFit: "contain",
    display: "block",
  },

  placeholder: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    gap: "10px",
    height: "100%",
    width: "100%",
  },

  placeholderText: {
    margin: 0,
    fontSize: "0.8rem",
    color: "#aab",
  },

  // ── Spinner ──
  spinner: {
    width: "32px",
    height: "32px",
    border: "3px solid #dde",
    borderTopColor: "#002353",
    borderRadius: "50%",
    animation: "spin 0.8s linear infinite",
  },

  // ── Button ──
  button: {
    margin: "12px 14px 4px",
    padding: "8px 16px",
    fontSize: "0.82rem",
    fontWeight: 600,
    letterSpacing: "0.02em",
    color: "#fff",
    backgroundColor: "#002353",
    border: "none",
    borderRadius: "6px",
    cursor: "pointer",
    alignSelf: "flex-start",
    transition: "background 0.15s, opacity 0.15s",
  },

  buttonDisabled: {
    opacity: 0.55,
    cursor: "not-allowed",
  },

  buttonLoaded: {
    backgroundColor: "#1a6e3c",
  },

  // ── Caption ──
  caption: {
    padding: "8px 14px 14px",
    fontSize: "0.78rem",
    color: "#556",
    lineHeight: 1.4,
    fontStyle: "italic",
  },
};

// Inject keyframes once into the document head (safe to call multiple times)
if (typeof document !== "undefined") {
  const styleId = "__graph-grid-styles__";
  if (!document.getElementById(styleId)) {
    const tag = document.createElement("style");
    tag.id = styleId;
    tag.textContent = `@keyframes spin { to { transform: rotate(360deg); } }`;
    document.head.appendChild(tag);
  }
}

export default chronosCard;
