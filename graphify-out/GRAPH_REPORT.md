# Graph Report - Gent-Terneuzen-canal  (2026-08-24)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 335 nodes · 432 edges · 33 communities (25 shown, 8 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS · INFERRED: 2 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `5a38b483`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- App.jsx
- main.py
- dependencies
- devDependencies
- pipeline_core.py
- EdgeDeepLearning.jsx
- timeseriesforecasting.py
- pipeline.py
- MapCard.jsx
- RDFTSS2LDES.py
- RDF2LDES_YMD_SPARQL_FOR_TSS.py
- RDF2TSS_V2.py
- preprocess_waterlink.py
- RDF2TSS_per_day_V1.py
- main
- ingest.py
- automated_alignments.py
- test.py
- preprocess.py
- preprocess2.py
- RML_generator.py
- SHACL_validate.py
- python.worker.js

## God Nodes (most connected - your core abstractions)
1. `main()` - 16 edges
2. `main()` - 9 edges
3. `main()` - 7 edges
4. `LSTMInference()` - 7 edges
5. `main()` - 7 edges
6. `main()` - 5 edges
7. `main()` - 5 edges
8. `scripts` - 5 edges
9. `getLdesState()` - 5 edges
10. `create_ldes_files()` - 4 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `build_lstm_autoencoder()`  [INFERRED]
  time_series_analysis/LSTM-train.py → time_series_analysis/train_lstm.py
- `main()` --calls--> `create_sequences()`  [INFERRED]
  time_series_analysis/LSTM-train.py → time_series_analysis/train_lstm.py
- `DataVisualization()` --calls--> `getLdesState()`  [EXTRACTED]
  frontend/src/components/datavisualization.jsx → frontend/src/components/LDESClientCard.jsx

## Import Cycles
- None detected.

## Communities (33 total, 8 thin omitted)

### Community 0 - "App.jsx"
Cohesion: 0.05
Nodes (30): App(), BenchmarksCardBody(), BenchmarksCardHead(), BodyCard(), BrowseDataBody(), BrowseDataHead(), headStyles, innerStyles (+22 more)

### Community 1 - "main.py"
Cohesion: 0.10
Nodes (13): FastAPI, get, chronos2forecast_visualization(), comparison_visualization(), ensemble_visualization(), lifespan(), lightGBM_visualization(), plot_sensor_data() (+5 more)

### Community 2 - "dependencies"
Cohesion: 0.06
Nodes (33): buffer, echarts, echarts-for-react, dependencies, buffer, echarts, echarts-for-react, ldes-client (+25 more)

### Community 3 - "devDependencies"
Cohesion: 0.06
Nodes (30): eslint, @eslint/js, eslint-plugin-react-hooks, eslint-plugin-react-refresh, devDependencies, eslint, @eslint/js, eslint-plugin-react-hooks (+22 more)

### Community 5 - "EdgeDeepLearning.jsx"
Cohesion: 0.14
Nodes (19): DataVisualization(), getSensorDataCache(), PREFIXES, sensorDataRegistry, buildAverageSeries(), buildForecastTimestamps(), extractSensorData(), ldesState (+11 more)

### Community 6 - "timeseriesforecasting.py"
Cohesion: 0.23
Nodes (16): comparison_visualization(), comparisonforecast(), datapreparation(), ensemble(), ensemble_visualization(), featureengineering(), identify_unique_sensors(), lightGBM_forecast_bias() (+8 more)

### Community 7 - "pipeline.py"
Cohesion: 0.29
Nodes (9): main(), setup_environment(), step_1_fetch_data(), step_1_pre_process_waterlink(), step_2_preprocess(), step_2_rml_mapping_waterlink(), step_3_rml_mapping(), step_4_ingest_virtuoso() (+1 more)

### Community 8 - "MapCard.jsx"
Cohesion: 0.18
Nodes (5): headStyles, innerStyles, MapCardBody(), MapCardHead(), styles

### Community 9 - "RDFTSS2LDES.py"
Cohesion: 0.33
Nodes (9): create_base_graph(), create_ldes_files(), delete_ldes_files(), delete_log(), divide_data(), load_graph(), main(), process_graph() (+1 more)

### Community 10 - "RDF2LDES_YMD_SPARQL_FOR_TSS.py"
Cohesion: 0.38
Nodes (9): create_base_graph(), create_ldes_files(), delete_ldes_files(), delete_log(), divide_data(), load_graph(), main(), process_graph() (+1 more)

### Community 11 - "RDF2TSS_V2.py"
Cohesion: 0.33
Nodes (8): create_sensor_set(), create_tss(), load_graph(), main(), Loads a Turtle file into an RDFLib Graph., Identifies unique sensors within the graph using a SPARQL query., Transforms sensor observations into the Time Series Snippets (TSS) format., save_graph()

### Community 12 - "preprocess_waterlink.py"
Cohesion: 0.32
Nodes (7): build_combined_header(), clean_result_sheet(), combine_datetime(), Cleans the 'result' tab of data.xlsx.  Assumed raw layout (1-indexed rows/cols, Combine a date value and a time value into a single ISO-8601 string,     e.g. ', Combine the description / attribute name / unit of measure (rows 1, 2, 3)     i, Reads `sheet_name` from `input_path`, merges the Datum/Tijd columns into     a

### Community 14 - "RDF2TSS_per_day_V1.py"
Cohesion: 0.60
Nodes (5): CreateSensorSet(), CreateTSS(), LoadGraph(), main(), SaveGraph()

### Community 15 - "main"
Cohesion: 0.40
Nodes (4): main(), build_lstm_autoencoder(), create_sequences(), dataset : (n_samples, 1) scaled array     Returns       X : (samples, time_ste

### Community 16 - "ingest.py"
Cohesion: 0.60
Nodes (4): delete_graph(), main(), Removes the entire named graph from Virtuoso., upload_graph()

## Knowledge Gaps
- **57 isolated node(s):** `buttonStyle`, `buttonStyle`, `headStyles`, `innerStyles`, `tableStyles` (+52 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `dependencies` connect `dependencies` to `devDependencies`?**
  _High betweenness centrality (0.026) - this node is a cross-community bridge._
- **What connects `buttonStyle`, `buttonStyle`, `headStyles` to the rest of the system?**
  _57 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `App.jsx` be split into smaller, more focused modules?**
  _Cohesion score 0.05333333333333334 - nodes in this community are weakly interconnected._
- **Should `main.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09982174688057041 - nodes in this community are weakly interconnected._
- **Should `dependencies` be split into smaller, more focused modules?**
  _Cohesion score 0.06060606060606061 - nodes in this community are weakly interconnected._
- **Should `devDependencies` be split into smaller, more focused modules?**
  _Cohesion score 0.06451612903225806 - nodes in this community are weakly interconnected._
- **Should `pipeline_core.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09881422924901186 - nodes in this community are weakly interconnected._