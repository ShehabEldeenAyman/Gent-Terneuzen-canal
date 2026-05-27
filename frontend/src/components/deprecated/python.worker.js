// src/python.worker.js
import { loadPyodide } from "pyodide";

// 1. Initialize Pyodide and load standard, WASM-compatible packages
let pyodideReadyPromise = (async () => {
  const pyodideInstance = await loadPyodide({
    indexURL: "https://cdn.jsdelivr.net/pyodide/v0.29.4/full/" 
  });
  
  // Load packages present in the official Pyodide repository
  await pyodideInstance.loadPackage(["numpy", "pandas", "matplotlib"]);
  
  return pyodideInstance;
})();

self.onmessage = async (event) => {
  // Wait for Pyodide and core packages to be ready
  const pyodide = await pyodideReadyPromise;
  const { code, context } = event.data;

  try {
    // Optional: Inject JavaScript variables into the Python scope
    if (context) {
      for (const key in context) {
        pyodide.globals.set(key, context[key]);
      }
    }

    // Run the Python code string
    await pyodide.runPythonAsync(code);
    
    // Extract the generated values out of Python's global scope
    const base64Image = pyodide.globals.get("img_base64");
    const outputLog = pyodide.globals.get("output_log");
    
    // Send the structured results back to the React component
    self.postMessage({ 
      success: true, 
      results: outputLog ? outputLog.toString() : "Execution complete.", 
      image: base64Image ? base64Image.toString() : null
    });
  } catch (error) {
    self.postMessage({ success: false, error: error.message });
  }
};