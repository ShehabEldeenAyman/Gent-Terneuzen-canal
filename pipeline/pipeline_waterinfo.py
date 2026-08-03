import pipeline_core as core
from rdflib import URIRef

GRAPH_URI = "http://example.com/Gent-Terneuzen"
DATA_DICTIONARY = {
    "waterinfo": ["289435042", "289423042", "289429042", "289441042"],
}
START_DATE = "2025-01-01T00:00:00Z"
END_DATE = "2026-03-31T23:59:59Z"

def main():
    core.setup_environment()
    for key,value in DATA_DICTIONARY.items():
        print (f"--- Processing parameter: {key} ---")
        print (f"--- Associated sensor IDs: {value} ---")
        print(f"value type: {type(value)}")
        print (f"--- Fetching data from {START_DATE} to {END_DATE} ---")
        core.step_1_fetch_data(START_DATE, END_DATE,value, parameter_name=key)
        core.step_2_preprocess(parameter_name=key)
        core.step_3_rml_mapping(parameter_name=key)

        print("--- Shacl in validation started ---")
        core.step_shacl_validate(f"../data/{key}.ttl","../SHACL/SHACL_in.ttl",f"../data/{key}_shacl_in_report.txt")
        print("--- Shacl in validation finished ---")


        print("--- Automated Aligments started ---")
        core.step_3_5_automating_alignments(f"../data/{key}.ttl",URIRef("http://qudt.org/vocab/unit/MilliS-PER-CentiM"))
        print("--- Automated Aligments finished ---")

        print("--- Shacl out validation started ---")
        core.step_shacl_validate(f"../data/{key}.ttl","../SHACL/SHACL_out.ttl",f"../data/{key}_shacl_out_report.txt")
        print("--- Shacl out validation finished ---")

        core.step_4_ingest_virtuoso(f"../data/{key}.ttl", GRAPH_URI, delete_existing=False)
        core.step_5_rdf2tss(f"../data/{key}.ttl", f"../data/{key}_tss.ttl",f"Data/{key}")

        print("--- Starting LDES File Generation Process---")
        core.step_6_RDF2LDES("water-info","data/waterinfo_tss.ttl","../data/water_info_ldes","../data/water_info_ldes")
        print("---  LDES File Generation Process Finished---")


if __name__ == "__main__":
    main()
