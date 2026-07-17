import pipeline_core as core
import sys; sys.path.append('..')  # Adds the parent directory
import python_backend_server.constants as constants

def main():
    core.setup_environment()
    print("--- Pre-Processing Water-Link Data started---")
    core.step_1_pre_process_waterlink("../data/water-link/data.xlsx","../data/water_link.csv")
    print("--- Pre-Processing Water-Link Data finished---")
    print("--- RML Mapping Water-Link Data started---")
    core.step_2_rml_mapping_waterlink("water_link")
    print("--- RML Mapping Water-Link Data finished---")
    core.step_5_rdf2tss("../data/water_link.ttl", "../data/conductivity_tss.ttl","Data/conductivity",overwrite=False)
    print("--- Ingesting Water-Link Data to Virtuoso started---")
    core.step_4_ingest_virtuoso("../data/water_link.ttl", constants.GRAPH_URI, delete_existing=False)
    print("--- Ingesting Water-Link Data to Virtuoso finished---")

if __name__ == "__main__":
    main()