# Graph Report - Gent-Terneuzen-canal  (2026-07-30)

## Corpus Check
- 69 files · ~292,867 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 344 nodes · 437 edges · 46 communities (32 shown, 14 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS · INFERRED: 2 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `5a38b483`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- main.py
- dependencies
- devDependencies
- EdgeDeepLearning.jsx
- App.jsx
- pipeline_core.py
- timeseriesforecasting.py
- pipeline.py
- MapCard.jsx
- RDFTSS2LDES.py
- RDF2LDES_YMD_SPARQL_FOR_TSS.py
- BrowseData.jsx
- RDF2TSS_V2.py
- start_preprocessing.py
- RDF2TSS_per_day_V1.py
- main
- chronosCard.jsx
- machineLearningCard.jsx
- ingest.py
- test.py
- QueryCard.jsx
- preprocess.py
- RML_generator.py
- data_fetch/__init__.py
- eslint.config.js
- vite.config.js
- pipeline/__init__.py
- Codex Repository Context
- QueryCard.jsx
- LDESChart.jsx
- LDESTSSChart.jsx
- SQLChart.jsx
- TTLChart.jsx
- frontend/README.md
- README.md

## God Nodes (most connected - your core abstractions)
1. `main()` - 16 edges
2. `main()` - 9 edges
3. `main()` - 7 edges
4. `main()` - 7 edges
5. `LSTMInference()` - 7 edges
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

## Communities (46 total, 14 thin omitted)

### Community 0 - "main.py"
Cohesion: 0.21
Nodes (8): App(), BenchmarksCardBody(), BenchmarksCardHead(), BodyCard(), ChartCardBody(), ChartCardHead(), CustomTensorflowBrowser(), tensorflowbrowser()

### Community 1 - "dependencies"
Cohesion: 0.10
Nodes (13): FastAPI, get, chronos2forecast_visualization(), comparison_visualization(), ensemble_visualization(), lifespan(), lightGBM_visualization(), plot_sensor_data() (+5 more)

### Community 2 - "devDependencies"
Cohesion: 0.06
Nodes (33): buffer, echarts, echarts-for-react, dependencies, buffer, echarts, echarts-for-react, ldes-client (+25 more)

### Community 3 - "EdgeDeepLearning.jsx"
Cohesion: 0.06
Nodes (30): eslint, @eslint/js, eslint-plugin-react-hooks, eslint-plugin-react-refresh, devDependencies, eslint, @eslint/js, eslint-plugin-react-hooks (+22 more)

### Community 5 - "pipeline_core.py"
Cohesion: 0.24
Nodes (9): DataVisualization(), getSensorDataCache(), PREFIXES, sensorDataRegistry, getLdesState(), LDESClientCard(), ldesRegistry, sensor_data (+1 more)

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

### Community 11 - "BrowseData.jsx"
Cohesion: 0.33
Nodes (8): create_sensor_set(), create_tss(), load_graph(), main(), Loads a Turtle file into an RDFLib Graph., Identifies unique sensors within the graph using a SPARQL query., Transforms sensor observations into the Time Series Snippets (TSS) format., save_graph()

### Community 12 - "RDF2TSS_V2.py"
Cohesion: 0.32
Nodes (7): build_combined_header(), clean_result_sheet(), combine_datetime(), Cleans the 'result' tab of data.xlsx.  Assumed raw layout (1-indexed rows/cols, Combine a date value and a time value into a single ISO-8601 string,     e.g. ', Combine the description / attribute name / unit of measure (rows 1, 2, 3)     i, Reads `sheet_name` from `input_path`, merges the Datum/Tijd columns into     a

### Community 14 - "start_preprocessing.py"
Cohesion: 0.60
Nodes (5): CreateSensorSet(), CreateTSS(), LoadGraph(), main(), SaveGraph()

### Community 15 - "RDF2TSS_per_day_V1.py"
Cohesion: 0.40
Nodes (4): main(), build_lstm_autoencoder(), create_sequences(), dataset : (n_samples, 1) scaled array     Returns       X : (samples, time_ste

### Community 16 - "main"
Cohesion: 0.60
Nodes (4): delete_graph(), main(), Removes the entire named graph from Virtuoso., upload_graph()

### Community 33 - "data_fetch/__init__.py"
Cohesion: 0.31
Nodes (10): buildAverageSeries(), buildForecastTimestamps(), extractSensorData(), ldesState, LSTMInference(), minMaxInverse(), minMaxScale(), PREFIXES (+2 more)

### Community 34 - "eslint.config.js"
Cohesion: 0.20
Nodes (5): BrowseDataBody(), BrowseDataHead(), headStyles, innerStyles, tableStyles

### Community 35 - "vite.config.js"
Cohesion: 0.40
Nodes (3): chronosCard(), GRAPH_ITEMS, styles

### Community 36 - "pipeline/__init__.py"
Cohesion: 0.40
Nodes (3): GRAPH_ITEMS, machineLearningCard(), styles

### Community 37 - "Codex Repository Context"
Cohesion: 0.50
Nodes (3): Codex Repository Context, Instructions for Codex, System Architecture & Topology

### Community 38 - "QueryCard.jsx"
Cohesion: 0.50
Nodes (3): innerStyles, QueryCard(), queryTemplates

## Knowledge Gaps
- **61 isolated node(s):** `name`, `private`, `version`, `type`, `dev` (+56 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `dependencies` connect `devDependencies` to `EdgeDeepLearning.jsx`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **What connects `name`, `private`, `version` to the rest of the system?**
  _61 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `dependencies` be split into smaller, more focused modules?**
  _Cohesion score 0.09982174688057041 - nodes in this community are weakly interconnected._
- **Should `devDependencies` be split into smaller, more focused modules?**
  _Cohesion score 0.06060606060606061 - nodes in this community are weakly interconnected._
- **Should `EdgeDeepLearning.jsx` be split into smaller, more focused modules?**
  _Cohesion score 0.06451612903225806 - nodes in this community are weakly interconnected._
- **Should `App.jsx` be split into smaller, more focused modules?**
  _Cohesion score 0.09881422924901186 - nodes in this community are weakly interconnected._