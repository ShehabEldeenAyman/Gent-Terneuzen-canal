---
type: "query"
date: "2026-08-12T12:51:23.526728+00:00"
question: "Why is the cross-correlation profile graph empty in lag_analysis_fuseki.ipynb?"
contributor: "graphify"
outcome: "useful"
source_nodes: ["lag()", ".observations()", "FusekiClient"]
---

# Q: Why is the cross-correlation profile graph empty in lag_analysis_fuseki.ipynb?

## Answer

Expanded from original query via graph vocabulary: [lag, observations, sensors, fuseki, graph]. The notebook configured the Indusii target as http://example.com/waterinfo/111111111, while Fuseki returns http://example.com/waterlink/111111111. The membership guard therefore skipped all four station calculations and left lag_results empty. Correcting the target namespace produces four lag profiles. The Waterinfo identifiers for Terneuzen and Gent-far were also swapped and were corrected; a fail-fast missing-sensor check now prevents silent empty plots.

## Outcome

- Signal: useful

## Source Nodes

- lag()
- .observations()
- FusekiClient