---
type: "query"
date: "2026-08-12T11:13:35.574373+00:00"
question: "Create a copy of lag_analysis.ipynb that reads from Apache Jena Fuseki using the correct graph and connection URI"
contributor: "graphify"
outcome: "useful"
source_nodes: ["query_url(),FusekiClient,upload_graph(),lag_analysis()"]
---

# Q: Create a copy of lag_analysis.ipynb that reads from Apache Jena Fuseki using the correct graph and connection URI

## Answer

Created time_series_analysis/lag_analysis_fuseki.ipynb while preserving the original. Expanded via graph vocabulary: [fuseki, jena, virtuoso, query, graph, observations, sparql, analytics, lag, constants]. The copy defaults to FUSEKI_DATA_URL=http://localhost:3030/dataset/data, derives FUSEKI_QUERY_URL=http://localhost:3030/dataset/query, and queries named graph http://example.com/Gent-Terneuzen. It supports FUSEKI_QUERY_URL, FUSEKI_DATA_URL, and ANALYTICS_DEFAULT_GRAPH_URI overrides, uses a POST SPARQL SELECT over GRAPH, and clears stale Virtuoso outputs. Live ASK verified the named graph contains data.

## Outcome

- Signal: useful

## Source Nodes

- query_url(),FusekiClient,upload_graph(),lag_analysis()