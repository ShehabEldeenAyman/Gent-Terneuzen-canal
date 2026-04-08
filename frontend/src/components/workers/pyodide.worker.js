// public/pyodide.worker.js
importScripts("https://cdn.jsdelivr.net/pyodide/v0.25.1/full/pyodide.js");

let pyodide = null;

async function initPyodide() {
  pyodide = await loadPyodide();
  // Install any Python packages you need, e.g. pandas, rdflib
  await pyodide.loadPackage(["micropip"]);
  await pyodide.runPythonAsync(`
    import micropip
    await micropip.install("rdflib")
  `);
  self.postMessage({ type: "ready" });
}

initPyodide();

self.onmessage = async (event) => {
  const { type, payload } = event.data;

  if (type === "process_member") {
    // payload.quads is the array of serialised quad objects
    const quads = payload.quads;

    // Inject quads into Python scope
    pyodide.globals.set("quads_json", JSON.stringify(quads));

    const result = await pyodide.runPythonAsync(`
      import json
      from rdflib import Graph, URIRef, Literal, BNode

      quads = json.loads(quads_json)
      g = Graph()

      for q in quads:
          def parse_term(t):
              tt = t.get("termType", "")
              v  = t.get("value", "")
              if tt == "NamedNode":
                  return URIRef(v)
              elif tt == "Literal":
                  return Literal(v)
              else:
                  return BNode(v)

          s = parse_term(q["subject"])
          p = parse_term(q["predicate"])
          o = parse_term(q["object"])
          g.add((s, p, o))

      # Example: return Turtle serialisation of this member's graph
      g.serialize(format="turtle")
    `);

    self.postMessage({
      type:    "result",
      id:      payload.id,
      turtle:  result,
    });
  }
};