"""Apache Jena Fuseki graph-store client used by the pipeline."""

import os

import requests


FUSEKI_DATA_URL = os.getenv("FUSEKI_DATA_URL", "http://localhost:3030/dataset/data")


def get_query_url():
    """Resolve Fuseki's read-only SPARQL query endpoint from the data endpoint."""
    configured = os.getenv("FUSEKI_QUERY_URL")
    if configured:
        return configured
    return FUSEKI_DATA_URL.rsplit("/data", 1)[0] + "/query"


def upload_graph(ttl_data_path, graph_uri):
    """Upload a Turtle file into a named graph and report an actionable result."""
    try:
        with open(ttl_data_path, "rb") as source:
            response = requests.post(
                FUSEKI_DATA_URL,
                params={"graph": graph_uri},
                data=source,
                headers={"Content-Type": "text/turtle"},
                timeout=60,
            )
        if response.status_code in (200, 201, 204):
            print(f"Uploaded {ttl_data_path} to Fuseki graph {graph_uri}")
            return True
        print(f"Fuseki upload failed ({response.status_code}): {response.text}")
    except FileNotFoundError:
        print(f"Turtle file not found: {ttl_data_path}")
    except requests.RequestException as error:
        print(f"Fuseki upload request failed: {error}")
    return False


def delete_graph(graph_uri):
    """Remove a named graph from Fuseki's Graph Store Protocol endpoint."""
    try:
        response = requests.delete(FUSEKI_DATA_URL, params={"graph": graph_uri}, timeout=30)
        if response.status_code in (200, 204):
            print(f"Deleted Fuseki graph {graph_uri}")
            return True
        print(f"Fuseki graph deletion failed ({response.status_code}): {response.text}")
    except requests.RequestException as error:
        print(f"Fuseki graph deletion request failed: {error}")
    return False
