import requests
USERNAME = "dba"
PASSWORD = "dba"
ttl_timeseries_path = "../data/timeseries.ttl"
ttl_stations_path = "../data/stations.ttl"
VIRTUOSO_URL = "http://localhost:8890/sparql-graph-crud"
GRAPH_URI = "http://example.com/Gent-Terneuzen"


def upload_graph(ttl_data_path):
    # 1. Prepare parameters and headers
    params = {'graph-uri': GRAPH_URI}
    headers = {'Content-Type': 'text/turtle'}
    print(f"started uploading {ttl_data_path} to {GRAPH_URI}")
    try:
        # 2. Open the file in binary mode and stream it
        with open(ttl_data_path, 'rb') as f:
            response = requests.post(
                VIRTUOSO_URL, 
                params=params, 
                data=f, 
                headers=headers, 
                auth=(USERNAME, PASSWORD)
            )

        # 3. Check result
        if response.status_code in [200, 201, 204]:
            print(f"Successfully uploaded {ttl_data_path} to {GRAPH_URI}")
        else:
            print(f"Failed to upload. Status code: {response.status_code}")
            print(f"Response: {response.text}")

    except FileNotFoundError:
        print(f"Error: The file at {ttl_data_path} was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

def delete_graph():
    """Removes the entire named graph from Virtuoso."""
    params = {'graph-uri': GRAPH_URI}
    
    try:
        print(f"Attempting to delete graph: {GRAPH_URI}...")
        response = requests.delete(
            VIRTUOSO_URL,
            params=params,
            auth=(USERNAME, PASSWORD)
        )
        
        # 200 (OK) or 204 (No Content) usually indicates success
        if response.status_code in [200, 204]:
            print(f"Successfully deleted graph: {GRAPH_URI}")
            return True
        else:
            print(f"Failed to delete graph. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"An error occurred during deletion: {e}")
        return False

def main():
    delete_graph()
    upload_graph(ttl_timeseries_path)
    upload_graph(ttl_stations_path)


if __name__ == "__main__":
    main()    