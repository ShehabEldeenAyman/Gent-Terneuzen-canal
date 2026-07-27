import pipeline_core as core
import sys; sys.path.append('..')  # Adds the parent directory
import python_backend_server.constants as constants
from rdflib import Graph,Namespace,URIRef,Literal

def main():
    core.setup_environment()
    for key,value in constants.data_dictionary.items():
        print (f"--- Processing parameter: {key} ---")
        print (f"--- Associated sensor IDs: {value} ---")
        print(f"value type: {type(value)}")
        print (f"--- Fetching data from {constants.START_DATE} to {constants.END_DATE} ---")
        core.step_1_fetch_data(constants.START_DATE, constants.END_DATE,value, parameter_name=key)
        core.step_2_preprocess(parameter_name=key)
        core.step_3_rml_mapping(parameter_name=key)
        print("--- Automated Aligments started ---")
        core.step_3_5_automating_alignments(f"../data/{key}.ttl",URIRef("http://qudt.org/vocab/unit/MilliS-PER-CentiM"))
        print("--- Automated Aligments finished ---")
        core.step_4_ingest_virtuoso(f"../data/{key}.ttl", constants.GRAPH_URI, delete_existing=False)
        core.step_5_rdf2tss(f"../data/{key}.ttl", f"../data/{key}_tss.ttl",f"Data/{key}")

if __name__ == "__main__":
    main()