import sys
import subprocess
import time
import os

# Setup paths (as defined in your notebook Step 1)
def setup_environment():
    sys.path.insert(0, "../data_fetch")
    sys.path.insert(0, "../pre_processing")
    sys.path.insert(0, "../triple_store_ingestion")
    sys.path.insert(0, "../RDF2TSS_V2")
    sys.path.insert(0, "../RDF2LDES")

def step_1_fetch_data(START_DATE, END_DATE):
    print("--- Step 1: Fetching Data ---")
    import fetch
    fetch.fetch_stations()
    fetch.fetch_timeseries(START_DATE, END_DATE)

def step_2_preprocess():
    print("--- Step 2: Pre-Processing ---")
    import preprocess
    preprocess.preprocess()

def step_3_rml_mapping():
    print("--- Step 3: RML-Mapping ---")
    command = [
        "java", 
        "-jar", "rmlmapper.jar", 
        "-m", "../RML_mapping/timeseriesmapping.rml.ttl", 
        "-o", "../data/timeseries.ttl", 
        "-s", "turtle"
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print("RML Mapping completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"RML Mapping failed: {e.stderr}")
        return False

def step_4_ingest_virtuoso(ttl_timeseries, graph_uri,delete_existing=True):
    print("--- Step 4: Ingesting to Virtuoso ---")
    import ingest
    if delete_existing:
        ingest.delete_graph(graph_uri)
    ingest.upload_graph(ttl_timeseries, graph_uri)
    #ingest.upload_graph(ttl_stations, graph_uri)

def step_5_rdf2tss(input_path, output_path):
    print("--- Step 5: RDF2TSS ---")
    import RDF2TSS_V2
    original_graph = RDF2TSS_V2.load_graph(input_path)
    sensor_set = RDF2TSS_V2.create_sensor_set(original_graph)
    tss_graph = RDF2TSS_V2.create_tss(sensor_set, original_graph)
    RDF2TSS_V2.save_graph(output_path, tss_graph)

def step_6_ingest_tss_virtuoso(tss_path, tss_graph_uri):
    print("--- Step 6: Ingesting TSS to Virtuoso ---")
    import ingest
    ingest.delete_graph(tss_graph_uri)
    ingest.upload_graph(tss_path, tss_graph_uri)

def step_7_transform_ldes(input_path):
    print("--- Step 7: Transforming to LDES ---")
    import RDFTSS2LDES
    start_time = time.perf_counter()
    
    original_graph = RDFTSS2LDES.load_graph(input_path)
    result = RDFTSS2LDES.process_graph(original_graph)
    RDFTSS2LDES.divide_data(result)
    
    # Clean up and create files
    RDFTSS2LDES.delete_log()
    RDFTSS2LDES.delete_ldes_files()
    RDFTSS2LDES.create_ldes_files()
    
    end_time = time.perf_counter()
    print(f"LDES Processing completed in {end_time - start_time:.2f} seconds.")

def catch_up():


def main():
    # Configuration
    GRAPH_URI = "http://example.com/Gent-Terneuzen"
    TSS_GRAPH_URI = "http://example.com/Gent-Terneuzen-TSS"
    
    TIMESERIES_TTL = "../data/timeseries.ttl"
    STATIONS_TTL = "../data/stations.ttl"
    TSS_GRAPH_TTL = "../data/TSSgraph.ttl"

    START_DATE = "2021-01-01T00:00:00Z"
    END_DATE = "2026-03-31T23:59:59Z"

    from_the_beginning = True  # Set to False to skip data fetching and preprocessing
    # Execution Pipeline
    setup_environment()
    if from_the_beginning:
        step_1_fetch_data(START_DATE, END_DATE)
        step_2_preprocess()
        step_3_rml_mapping()
        step_4_ingest_virtuoso(TIMESERIES_TTL, GRAPH_URI, delete_existing=False)
        step_5_rdf2tss(TIMESERIES_TTL, TSS_GRAPH_TTL)
        #step_6_ingest_tss_virtuoso(TSS_GRAPH_TTL, TSS_GRAPH_URI)          
        step_7_transform_ldes(TSS_GRAPH_TTL)

if __name__ == "__main__":
    main()