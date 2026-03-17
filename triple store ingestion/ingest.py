import requests
USERNAME = "dba"
PASSWORD = "dba"
timeseries_path = "../data/timeseries.ttl"
VIRTUOSO_URL = "http://localhost:8890/sparql-graph-crud"
GRAPH_URI = "http://example.com/Gent-Terneuzen"


def upload_graph():
    # 1. Prepare parameters and headers
    params = {'graph-uri': GRAPH_URI}
    headers = {'Content-Type': 'text/turtle'}

    try:
        # 2. Open the file in binary mode and stream it
        with open(timeseries_path, 'rb') as f:
            response = requests.put(
                VIRTUOSO_URL, 
                params=params, 
                data=f, 
                headers=headers, 
                auth=(USERNAME, PASSWORD)
            )

        # 3. Check result
        if response.status_code in [200, 201, 204]:
            print(f"Successfully uploaded {timeseries_path} to {GRAPH_URI}")
        else:
            print(f"Failed to upload. Status code: {response.status_code}")
            print(f"Response: {response.text}")

    except FileNotFoundError:
        print(f"Error: The file at {timeseries_path} was not found.")
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
    upload_graph()
    #delete_graph()

if __name__ == "__main__":
    main()    