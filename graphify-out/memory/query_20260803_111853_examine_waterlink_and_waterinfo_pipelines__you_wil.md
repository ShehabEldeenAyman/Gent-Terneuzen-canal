---
type: "query"
date: "2026-08-03T11:18:53.881846+00:00"
question: "examine waterlink and waterinfo pipelines, you will see that I have added a new feature which is RDF2LDES. can you integrate this new feature in the frontend similar to all the other features of the pipeline that you integrated before."
contributor: "graphify"
outcome: "useful"
source_nodes: ["step_6_RDF2LDES()", "stage_catalog()", "artifact()", "App()"]
---

# Q: examine waterlink and waterinfo pipelines, you will see that I have added a new feature which is RDF2LDES. can you integrate this new feature in the frontend similar to all the other features of the pipeline that you integrated before.

## Answer

Expanded from graph vocabulary: [rdf, ldes, pipeline, waterlink, waterinfo, stage, artifact, frontend, playground]. Integrated step_6_RDF2LDES into both playground stage catalogs and execution dispatches. pipeline_core now returns a generation summary and a bounded preview of TREE index and recent readings.trig artifacts. The React dashboard labels nested LDES artifacts distinctly, previews TriG source, and updates overview/data-browser copy. Both use cases report 9 stages with RDF2LDES available; Python compilation, backend contract checks, ESLint, and Vite production build pass.

## Outcome

- Signal: useful

## Source Nodes

- step_6_RDF2LDES()
- stage_catalog()
- artifact()
- App()