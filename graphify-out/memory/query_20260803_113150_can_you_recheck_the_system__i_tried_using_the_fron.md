---
type: "query"
date: "2026-08-03T11:31:50.816042+00:00"
question: "can you recheck the system, I tried using the front end testing the water-link use case. I ran step 1 just fine. in step 2 i got attention needed: name '_rml_mapping' is not defined."
contributor: "graphify"
outcome: "useful"
source_nodes: ["step_2_rml_mapping_waterlink()", "stage_result()", "_run()"]
---

# Q: can you recheck the system, I tried using the front end testing the water-link use case. I ran step 1 just fine. in step 2 i got attention needed: name '_rml_mapping' is not defined.

## Answer

Expanded from graph vocabulary: [rml, mapping, waterlink, pipeline, core, step, playground, server]. The frontend endpoint calls stage_result(), which calls step_2_rml_mapping_waterlink(); that wrapper referenced a missing _rml_mapping helper. Restored a shared _rml_mapping implementation that dynamically selects RML_generator_waterlink or RML_generator, generates the mapping, invokes rmlmapper.jar through _run(), and returns artifacts. The real frontend endpoint path now succeeds in 3.72 seconds and returns RML_mapping/water_link.rml.ttl plus data/water_link.ttl. Python compilation, ESLint, and Vite build pass.

## Outcome

- Signal: useful

## Source Nodes

- step_2_rml_mapping_waterlink()
- stage_result()
- _run()