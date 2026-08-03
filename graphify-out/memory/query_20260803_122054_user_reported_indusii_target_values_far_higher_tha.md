---
type: "query"
date: "2026-08-03T12:20:54.803515+00:00"
question: "User reported Indusii target values far higher than the four Waterinfo sensors and asked to fix suspected unit conversion before analysis."
contributor: "graphify"
outcome: "useful"
source_nodes: ["transform_unit_optimized()", "FusekiClient", ".observations()", "analysis.py"]
---

# Q: User reported Indusii target values far higher than the four Waterinfo sensors and asked to fix suspected unit conversion before analysis.

## Answer

Expanded via graph vocabulary: [waterlink, waterinfo, conductivity, unit, value, sensor, result, mapping, rml, ingestion, fuseki, scale]. The old transform_unit_optimized converted source values into the SI reference value but labelled them as the requested target unit. For microSiemens/cm to milliSiemens/cm it produced Siemens/m values, which are 10x too small. Repeated Water-Link ingestion also left raw and converted values plus two unit labels on each observation, which the analytics pivot averaged. Corrected the QUDT source-to-target formula, grouped Fuseki rows per observation, detected the legacy duplicate signature, normalized every selected series to mS/cm before every analysis, and exposed the normalization report in the frontend. Live medians now align around 15-18 mS/cm.

## Outcome

- Signal: useful

## Source Nodes

- transform_unit_optimized()
- FusekiClient
- .observations()
- analysis.py