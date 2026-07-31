import requests

# Update the URL to point to your new Fuseki dataset endpoint
VIRTUOSO_URL = "http://localhost:3030/dataset/data"  # Replace 'dataset' with your actual Fuseki dataset name
ttl_timeseries_path = "../data/timeseries.ttl"
ttl_stations_path = "../data/stations.ttl"


def upload_graph(ttl_data_path, GRAPH_URI):
    params = {'graph': GRAPH_URI}
    headers = {'Content-Type': 'text/turtle'}
    print(f"started uploading {ttl_data_path} to {GRAPH_URI}")
    try:
        with open(ttl_data_path, 'rb') as f:
            response = requests.post(
                VIRTUOSO_URL, 
                params=params, 
                data=f, 
                headers=headers
            )

        if response.status_code in [200, 201, 204]:
            print(f"Successfully uploaded {ttl_data_path} to {GRAPH_URI}")
        else:
            print(f"Failed to upload. Status code: {response.status_code}")
            print(f"Response: {response.text}")

    except FileNotFoundError:
        print(f"Error: The file at {ttl_data_path} was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


def delete_graph(GRAPH_URI):
    """Removes the entire named graph from the triplestore."""
    params = {'graph': GRAPH_URI}
    
    try:
        print(f"Attempting to delete graph: {GRAPH_URI}...")
        response = requests.delete(
            VIRTUOSO_URL,
            params=params
        )
        
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
    GRAPH_URI = "http://example.com/Gent-Terneuzen"
    delete_graph(GRAPH_URI)
    upload_graph(ttl_timeseries_path, GRAPH_URI)
    upload_graph(ttl_stations_path, GRAPH_URI)


if __name__ == "__main__":
    main()