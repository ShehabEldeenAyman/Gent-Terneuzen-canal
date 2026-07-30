import pipeline_core as core
import sys; sys.path.append('..')  # Adds the parent directory
import python_backend_server.constants as constants
from rdflib import Graph,Namespace,URIRef,Literal

def main():
    core.setup_environment()
    print("--- Pre-Processing Water-Link Data started---")
    core.step_1_pre_process_waterlink("../data/water-link/data.xlsx","../data/water_link.csv")
    print("--- Pre-Processing Water-Link Data finished---")
    print("--- RML Mapping Water-Link Data started---")
    core.step_2_rml_mapping_waterlink("water_link")
    print("--- RML Mapping Water-Link Data finished---")

    print("--- Shacl in validation started ---")
    core.step_shacl_validate("../data/water_link.ttl","../SHACL/SHACL_in.ttl","../data/water_link_shacl_in_report.txt")
    print("--- Shacl in validation finished ---")

    print("--- Automated Aligments started ---")
    core.step_3_5_automating_alignments("../data/water_link.ttl",URIRef("http://qudt.org/vocab/unit/MilliS-PER-CentiM"))
    print("--- Automated Aligments finished ---")

    print("--- Shacl out validation started ---")
    core.step_shacl_validate("../data/water_link.ttl","../SHACL/SHACL_out.ttl","../data/water_link_shacl_out_report.txt")
    print("--- Shacl out validation finished ---")

    core.step_5_rdf2tss("../data/water_link.ttl", "../data/waterlink_tss.ttl","Data/conductivity",overwrite=True)

    core.step_5_5_reasoner("../data/water_link.tt","../N3rules/rules.n3")

    print("--- Ingesting Water-Link Data to Virtuoso started---")
    core.step_4_ingest_virtuoso("../data/water_link.ttl", constants.GRAPH_URI, delete_existing=True)
    print("--- Ingesting Water-Link Data to Virtuoso finished---")

if __name__ == "__main__":
    main()