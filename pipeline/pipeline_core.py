import sys
import subprocess
import time
import os
from datetime import datetime, timezone
import sys; sys.path.append('..')  # Adds the parent directory
import python_backend_server.constants as constants


# Setup paths (as defined in your notebook Step 1)
def setup_environment():
    sys.path.insert(0, "../data_fetch")
    sys.path.insert(0, "../pre_processing")
    sys.path.insert(0, "../triple_store_ingestion")
    sys.path.insert(0, "../RDF2TSS_V2")
    sys.path.insert(0, "../RDF2LDES")
    sys.path.insert(0, "../RML_generator")

def step_1_fetch_data(START_DATE, END_DATE,timeseriesgroup_ids,parameter_name):
    print("--- Step 1: Fetching Data ---")
    import fetch
    #fetch.fetch_stations()
    fetch.fetch_timeseries(START_DATE, END_DATE,timeseriesgroup_ids,parameter_name)

def step_2_preprocess(parameter_name):
    print("--- Step 2: Pre-Processing ---")
    import preprocess
    preprocess.preprocess(parameter_name)
    preprocess.preprocess2(parameter_name)

def step_3_rml_mapping(parameter_name):
    print("--- Step 3: RML-Mapping ---")
    import RML_generator
    RML_generator.generate_timeseries_mapping(parameter_name)
    command = [
        "java", 
        "-jar", "rmlmapper.jar", 
        "-m", f"../RML_mapping/{parameter_name}.rml.ttl", 
        "-o", f"../data/{parameter_name}.ttl", 
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

def step_5_rdf2tss(input_path, output_path,observed_parameter="placeholder",overwrite=True):
    print("--- Step 5: RDF2TSS ---")
    import RDF2TSS_V2
    original_graph = RDF2TSS_V2.load_graph(input_path)
    sensor_set = RDF2TSS_V2.create_sensor_set(original_graph)
    tss_graph = RDF2TSS_V2.create_tss(sensor_set, original_graph,observed_parameter)
    RDF2TSS_V2.save_graph(output_path, tss_graph, overwrite)

def step_6_ingest_tss_virtuoso(tss_path, tss_graph_uri):
    print("--- Step 6: Ingesting TSS to Virtuoso ---")
    import ingest
    ingest.delete_graph(tss_graph_uri)
    ingest.upload_graph(tss_path, tss_graph_uri)

def step_7_transform_ldes(input_path,property_name="placeholder"):
    print("--- Step 7: Transforming to LDES ---")
    import RDFTSS2LDES
    start_time = time.perf_counter()
    RDFTSS2LDES.set_property(property_name, directory_input=f"../data/{property_name}/", base_path_input=f"../data/{property_name}")  # Call this function to set the property for LDES transformation
    original_graph = RDFTSS2LDES.load_graph(input_path)
    result = RDFTSS2LDES.process_graph(original_graph)
    RDFTSS2LDES.divide_data(result)
    
    # Clean up and create files
    RDFTSS2LDES.delete_log()
    RDFTSS2LDES.delete_ldes_files()
    RDFTSS2LDES.create_ldes_files()
    
    end_time = time.perf_counter()
    print(f"LDES Processing completed in {end_time - start_time:.2f} seconds.")

def step_1_pre_process_waterlink(input_path,output_path):
    import preprocess_waterlink
    preprocess_waterlink.clean_result_sheet(input_path,output_path)

def step_2_rml_mapping_waterlink(parameter_name):
    print("--- Step 3: RML-Mapping ---")
    import RML_generator_waterlink
    RML_generator_waterlink.generate_timeseries_mapping(parameter_name)
    command = [
        "java", 
        "-jar", "rmlmapper.jar", 
        "-m", f"../RML_mapping/{parameter_name}.rml.ttl", 
        "-o", f"../data/{parameter_name}.ttl", 
        "-s", "turtle"
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print("RML Mapping completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"RML Mapping failed: {e.stderr}")
        return False