# Graph Report - Gent-Terneuzen-canal  (2026-08-03)

## Corpus Check
- 82 files · ~300,458 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 480 nodes · 683 edges · 59 communities (42 shown, 17 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 14 edges (avg confidence: 0.61)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `0063ac42`
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
- preprocess_waterlink.py
- start_preprocessing.py
- RDF2TSS_per_day_V1.py
- chronosCard.jsx
- machineLearningCard.jsx
- ingest.py
- test.py
- QueryCard.jsx
- preprocess.py
- LDESTSSChart.jsx
- SQLChart.jsx
- preprocess2.py
- RML_generator.py
- pyodidetest.jsx
- python.worker.js
- GraphCard.jsx
- RML_generator_waterlink.py
- data_fetch/__init__.py
- eslint.config.js
- Codex Repository Context
- SQLChart.jsx
- README.md
- server.py
- analysis.py
- Q: Now using this document provided, can you add new subsection to the website explaining what is the usecase and what is the goal maybe add nice figure or an interactive map
- Q: examine waterlink and waterinfo pipelines, you will see that I have added a new feature which is RDF2LDES. can you integrate this new feature in the frontend similar to all the other features of the pipeline that you integrated before.
- Q: can you recheck the system, I tried using the front end testing the water-link use case. I ran step 1 just fine. in step 2 i got attention needed: name '_rml_mapping' is not defined.
- Lag analytics workspace
- pipeline/README.md

## God Nodes (most connected - your core abstractions)
1. `main()` - 16 edges
2. `stage_result()` - 13 edges
3. `FusekiClient` - 12 edges
4. `setup_environment()` - 11 edges
5. `machine_learning()` - 10 edges
6. `matrix_profile()` - 10 edges
7. `FusekiError` - 10 edges
8. `AnalysisRequest` - 10 edges
9. `main()` - 9 edges
10. `prepare_observations()` - 9 edges

## Surprising Connections (you probably didn't know these)
- `_frame()` --calls--> `prepare_observations()`  [EXTRACTED]
  lag_analytics_workspace/server.py → lag_analytics_workspace/analysis.py
- `lag()` --calls--> `lag_analysis()`  [EXTRACTED]
  lag_analytics_workspace/server.py → lag_analytics_workspace/analysis.py
- `ml()` --calls--> `machine_learning()`  [EXTRACTED]
  lag_analytics_workspace/server.py → lag_analytics_workspace/analysis.py
- `dl()` --calls--> `deep_learning()`  [EXTRACTED]
  lag_analytics_workspace/server.py → lag_analytics_workspace/analysis.py
- `profile()` --calls--> `matrix_profile()`  [EXTRACTED]
  lag_analytics_workspace/server.py → lag_analytics_workspace/analysis.py

## Import Cycles
- None detected.

## Communities (59 total, 17 thin omitted)

### Community 0 - "main.py"
Cohesion: 0.10
Nodes (13): FastAPI, chronos2forecast_visualization(), comparison_visualization(), ensemble_visualization(), lifespan(), lightGBM_visualization(), plot_sensor_data(), get (+5 more)

### Community 1 - "dependencies"
Cohesion: 0.06
Nodes (33): buffer, echarts, echarts-for-react, dependencies, buffer, echarts, echarts-for-react, ldes-client (+25 more)

### Community 2 - "devDependencies"
Cohesion: 0.06
Nodes (30): eslint, @eslint/js, eslint-plugin-react-hooks, eslint-plugin-react-refresh, devDependencies, eslint, @eslint/js, eslint-plugin-react-hooks (+22 more)

### Community 3 - "EdgeDeepLearning.jsx"
Cohesion: 0.14
Nodes (18): DataVisualization(), getSensorDataCache(), PREFIXES, sensorDataRegistry, buildAverageSeries(), buildForecastTimestamps(), extractSensorData(), ldesState (+10 more)

### Community 4 - "App.jsx"
Cohesion: 0.14
Nodes (23): data_path(), ldes_artifacts(), Reusable, observable stages for the canal data pipelines.  The functions in this, Run EYE and save inferred triples next to the source RDF file., Return a useful, bounded preview of a generated LDES tree.      A full run can c, Make pipeline collaborators importable without the forecasting server., Generate an RML mapping with the selected generator and run RMLMapper., _rml_mapping() (+15 more)

### Community 5 - "pipeline_core.py"
Cohesion: 0.18
Nodes (20): pipeline_working_directory(), Support legacy collaborators that resolve paths relative to pipeline/., active_calls(), artifact(), artifact_summary(), expected_artifacts(), fuseki_status(), list_use_cases() (+12 more)

### Community 6 - "timeseriesforecasting.py"
Cohesion: 0.23
Nodes (16): comparison_visualization(), comparisonforecast(), datapreparation(), ensemble(), ensemble_visualization(), featureengineering(), identify_unique_sensors(), lightGBM_forecast_bias() (+8 more)

### Community 7 - "pipeline.py"
Cohesion: 0.12
Nodes (14): ApiError(), App(), artifactLabel(), ArtifactPreview(), DataBrowser(), fallbackUseCases, icon(), PipelineRun() (+6 more)

### Community 8 - "MapCard.jsx"
Cohesion: 0.26
Nodes (9): main(), setup_environment(), step_1_fetch_data(), step_1_pre_process_waterlink(), step_2_preprocess(), step_2_rml_mapping_waterlink(), step_3_rml_mapping(), step_4_ingest_virtuoso() (+1 more)

### Community 9 - "RDFTSS2LDES.py"
Cohesion: 0.18
Nodes (3): headStyles, innerStyles, styles

### Community 10 - "RDF2LDES_YMD_SPARQL_FOR_TSS.py"
Cohesion: 0.33
Nodes (9): create_base_graph(), create_ldes_files(), delete_ldes_files(), delete_log(), divide_data(), load_graph(), main(), process_graph() (+1 more)

### Community 11 - "BrowseData.jsx"
Cohesion: 0.38
Nodes (9): create_base_graph(), create_ldes_files(), delete_ldes_files(), delete_log(), divide_data(), load_graph(), main(), process_graph() (+1 more)

### Community 12 - "RDF2TSS_V2.py"
Cohesion: 0.20
Nodes (3): headStyles, innerStyles, tableStyles

### Community 13 - "preprocess_waterlink.py"
Cohesion: 0.33
Nodes (8): create_sensor_set(), create_tss(), load_graph(), main(), Loads a Turtle file into an RDFLib Graph., Identifies unique sensors within the graph using a SPARQL query., Transforms sensor observations into the Time Series Snippets (TSS) format., save_graph()

### Community 14 - "start_preprocessing.py"
Cohesion: 0.32
Nodes (7): build_combined_header(), clean_result_sheet(), combine_datetime(), Cleans the 'result' tab of data.xlsx.  Assumed raw layout (1-indexed rows/cols, Combine a date value and a time value into a single ISO-8601 string,     e.g. ', Combine the description / attribute name / unit of measure (rows 1, 2, 3)     i, Reads `sheet_name` from `input_path`, merges the Datum/Tijd columns into     a

### Community 15 - "RDF2TSS_per_day_V1.py"
Cohesion: 0.25
Nodes (7): delete_graph(), get_query_url(), Apache Jena Fuseki graph-store client used by the pipeline., Resolve Fuseki's read-only SPARQL query endpoint from the data endpoint., Upload a Turtle file into a named graph and report an actionable result., Remove a named graph from Fuseki's Graph Store Protocol endpoint., upload_graph()

### Community 17 - "chronosCard.jsx"
Cohesion: 0.60
Nodes (5): CreateSensorSet(), CreateTSS(), LoadGraph(), main(), SaveGraph()

### Community 18 - "machineLearningCard.jsx"
Cohesion: 0.40
Nodes (4): main(), build_lstm_autoencoder(), create_sequences(), dataset : (n_samples, 1) scaled array     Returns       X : (samples, time_ste

### Community 21 - "QueryCard.jsx"
Cohesion: 0.50
Nodes (3): Codex Repository Context, Instructions for Codex, System Architecture & Topology

### Community 52 - "server.py"
Cohesion: 0.12
Nodes (29): _CacheEntry, FusekiClient, FusekiError, _iri(), DataFrame, query_url(), Small, read-only Apache Jena Fuseki client for the analytics workspace., Use the same Fuseki environment convention as triple_store_ingestion. (+21 more)

### Community 53 - "analysis.py"
Cohesion: 0.25
Nodes (20): deep_learning(), describe_data(), _feature_matrix(), lag_analysis(), machine_learning(), matrix_profile(), _number(), prepare_observations() (+12 more)

### Community 54 - "Q: Now using this document provided, can you add new subsection to the website explaining what is the usecase and what is the goal maybe add nice figure or an interactive map"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Now using this document provided, can you add new subsection to the website explaining what is the usecase and what is the goal maybe add nice figure or an interactive map, Source Nodes

### Community 55 - "Q: examine waterlink and waterinfo pipelines, you will see that I have added a new feature which is RDF2LDES. can you integrate this new feature in the frontend similar to all the other features of the pipeline that you integrated before."
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: examine waterlink and waterinfo pipelines, you will see that I have added a new feature which is RDF2LDES. can you integrate this new feature in the frontend similar to all the other features of the pipeline that you integrated before., Source Nodes

### Community 56 - "Q: can you recheck the system, I tried using the front end testing the water-link use case. I ran step 1 just fine. in step 2 i got attention needed: name '_rml_mapping' is not defined."
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: can you recheck the system, I tried using the front end testing the water-link use case. I ran step 1 just fine. in step 2 i got attention needed: name '_rml_mapping' is not defined., Source Nodes

### Community 57 - "Lag analytics workspace"
Cohesion: 0.50
Nodes (3): Fuseki configuration, Lag analytics workspace, Start

## Knowledge Gaps
- **77 isolated node(s):** `name`, `private`, `version`, `type`, `dev` (+72 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Work-memory lessons

**Preferred sources** — corroborated by past sessions; start here.
- `App()` (2× useful, score=1.934251097) _(code changed — re-verify)_

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `dependencies` connect `dependencies` to `devDependencies`?**
  _High betweenness centrality (0.013) - this node is a cross-community bridge._
- **Why does `FusekiError` connect `server.py` to `App.jsx`?**
  _High betweenness centrality (0.008) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `FusekiClient` (e.g. with `AnalysisRequest` and `DeepLearningRequest`) actually correct?**
  _`FusekiClient` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `name`, `private`, `version` to the rest of the system?**
  _77 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `main.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09982174688057041 - nodes in this community are weakly interconnected._
- **Should `dependencies` be split into smaller, more focused modules?**
  _Cohesion score 0.06060606060606061 - nodes in this community are weakly interconnected._
- **Should `devDependencies` be split into smaller, more focused modules?**
  _Cohesion score 0.06451612903225806 - nodes in this community are weakly interconnected._