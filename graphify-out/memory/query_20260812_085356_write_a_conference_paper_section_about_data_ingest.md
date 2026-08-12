---
type: "query"
date: "2026-08-12T08:53:56.702239+00:00"
question: "Write a conference-paper section about data ingestion and transformation to Linked Data using RML for this project"
contributor: "graphify"
outcome: "useful"
source_nodes: ["step_1_fetch_data(),step_1_pre_process_waterlink(),_rml_mapping(),generate_timeseries_mapping(),validate_shacl(),transform_unit_optimized(),step_4_ingest_triplestore(),upload_graph()"]
---

# Q: Write a conference-paper section about data ingestion and transformation to Linked Data using RML for this project

## Answer

Expanded from graph vocabulary: [waterinfo, waterlink, preprocess, rml, mapping, mapper, rdf, sosa, qudt, shacl, fuseki, ingestion]. The implemented pipeline acquires Waterinfo measurements through pywaterinfo and Water-Link observations from an Excel workbook, converts both to source-specific CSV tables with ISO-8601 timestamps, generates RML triples maps, and materializes Turtle RDF with RMLMapper. Both mappings produce SOSA observations with stable observation and sensor IRIs, xsd:dateTime result times, numeric simple results, QUDT ElectricConductivity semantics, and explicit conductivity units. SHACL validates the graph before and after QUDT-based conversion from micro-Siemens per centimetre to milli-Siemens per centimetre. Validated Turtle graphs are uploaded through the Graph Store Protocol into the shared Gent-Terneuzen named graph in Apache Jena Fuseki for SPARQL access. The graph preserves provider identity at sensor-IRI level but does not implement a complete provenance model.

## Outcome

- Signal: useful

## Source Nodes

- step_1_fetch_data(),step_1_pre_process_waterlink(),_rml_mapping(),generate_timeseries_mapping(),validate_shacl(),transform_unit_optimized(),step_4_ingest_triplestore(),upload_graph()