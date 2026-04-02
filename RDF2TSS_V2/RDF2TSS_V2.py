import json
import argparse
from rdflib import Graph, URIRef, Namespace, BNode, Literal
from rdflib.namespace import XSD, RDF, RDFS

# --- Configuration & Namespaces ---
EX = Namespace('http://example.com/attributes/')
OBS = Namespace('http://example.com/observations/')
RML = Namespace('http://w3id.org/rml/')
SOSA = Namespace('http://www.w3.org/ns/sosa/')
SSN = Namespace('http://www.w3.org/ns/ssn/')
WATERINFO = Namespace('http://example.com/waterinfo/')
TSS = Namespace('https://w3id.org/tss#')

BASE_SNIPPET = Namespace("https://example.org/tss/snippet/")
SENSOR_READING_ID = Namespace("https://example.org/tss/snippet/reading/")

def load_graph(directory):
    """Loads a Turtle file into an RDFLib Graph."""
    graph = Graph()
    print(f"Started loading graph from {directory}...")
    graph.parse(directory, format="turtle", publicID="https://example.org/")
    print("Graph loaded successfully.")
    return graph

def save_graph(directory, final_graph):
    """Serializes the graph to a Turtle file on disk."""
    print(f"Started writing file to disk: {directory}")
    final_graph.serialize(destination=directory, format="turtle")
    print("File written successfully.")

def create_sensor_set(graph):
    """Identifies unique sensors within the graph using a SPARQL query."""
    sensor_set = set()
    get_sensor_query = ''' 
    PREFIX sosa: <http://www.w3.org/ns/sosa/>
    SELECT DISTINCT ?sensor
    WHERE {
      ?s sosa:madeBySensor ?sensor .
    }
    '''
    print('Started identifying unique sensors...')
    for sensor in graph.query(get_sensor_query):
        sensor_term = sensor[0]
        sensor_set.add(sensor_term)

    print(f'{len(sensor_set)} Sensors identified successfully.')
    return sensor_set

def create_tss(sensor_set, graph):
    """Transforms sensor observations into the Time Series Snippets (TSS) format."""
    final_graph = Graph()

    # Bind prefixes for cleaner output
    prefixes = {
        'EX': EX, 'obs': OBS, 'rdf': RDF, 'rdfs': RDFS, 
        'rml': RML, 'sosa': SOSA, 'ssn': SSN, 
        'waterinfo': WATERINFO, 'xsd': XSD, 'tss': TSS
    }
    for prefix, ns in prefixes.items():
        final_graph.bind(prefix, ns)

    print("Started extracting observations per sensor...")

    for i, sensor in enumerate(sensor_set):
        print(f"Processing sensor {i+1}/{len(sensor_set)}")

        data_per_sensor_query = """
        PREFIX sosa: <http://www.w3.org/ns/sosa/>
        PREFIX ex: <http://example.com/attributes/>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

        SELECT ?OBSERVATION ?TIME ?READING ?qualityCode ?qualityName ?qualityDesc ?qualityColor ?interpolation
        WHERE {
            ?OBSERVATION a sosa:Observation ;
                        sosa:resultTime ?TIME ;
                        sosa:hasSimpleResult ?READING ;
                        sosa:madeBySensor ?currentSensor .
                        OPTIONAL { ?OBSERVATION ex:qualityCode ?qualityCode }
                        OPTIONAL { ?OBSERVATION ex:qualityCodeName ?qualityName }
                        OPTIONAL { ?OBSERVATION ex:qualityCodeDescription ?qualityDesc }
                        OPTIONAL { ?OBSERVATION ex:qualityCodeColor ?qualityColor }
                        OPTIONAL { ?OBSERVATION ex:interpolationType ?interpolation }
        }
        ORDER BY ?TIME
        """
        
        results = graph.query(data_per_sensor_query, initBindings={'currentSensor': sensor})
        results_list = list(results)
        
        if not results_list:
            continue

        sensor_json_array = []
        for row in results_list:
            observation_json_object = {
                "id": str(SENSOR_READING_ID[f"{i}"]),
                "time": str(row.TIME),
                "value": float(row.READING),
                # "interpolationType": str(row.interpolation),
                # "qualityCode": int(row.qualityCode),
                # "qualityCodeColor": str(row.qualityColor),
                # "qualityCodeDescription": str(row.qualityDesc),
                # "qualityCodeName": str(row.qualityDesc)
            }
            sensor_json_array.append(observation_json_object)

        json_output = json.dumps(sensor_json_array, indent=1)

        # Context definition for the TSS literal
        context_data = {
            "@context": {
                "id": "@id",
                "time": {"@id": str(SOSA.resultTime), "@type": str(XSD.dateTime)},
                "value": {"@id": str(SOSA.hasSimpleResult), "@type": str(XSD.double)},
                # "interpolationType": {"@id": str(EX.interpolationType), "@type": str(XSD.string)},
                # "qualityCode": {"@id": str(EX.qualityCode), "@type": str(XSD.integer)},
                # "qualityCodeColor": {"@id": str(EX.qualityCodeColor), "@type": str(XSD.string)},
                # "qualityCodeDescription": {"@id": str(EX.qualityCodeDescription), "@type": str(XSD.string)},
                # "qualityCodeName": {"@id": str(EX.qualityCodeName), "@type": str(XSD.string)}
            }
        }
        context_data_dump = json.dumps(context_data, indent=1)

        # RDF construction
        snippet = URIRef(BASE_SNIPPET[f"{sensor}"])
        template = BNode()

        final_graph.add((snippet, RDF.type, TSS.Snippet))
        final_graph.add((snippet, TSS["from"], results_list[0].TIME))
        final_graph.add((snippet, TSS["until"], results_list[-1].TIME))
        final_graph.add((snippet, TSS.points, Literal(json_output, datatype=RDF.JSON)))
        final_graph.add((snippet, TSS.about, template))
        final_graph.add((snippet, TSS.context, Literal(context_data_dump, datatype=RDF.JSON)))
        
        final_graph.add((template, RDF.type, TSS.PointTemplate))
        final_graph.add((template, SOSA.madeBySensor, sensor))
        final_graph.add((template, SOSA.observedProperty, WATERINFO.Conductivity))
    
    print("TSS graph creation complete.")
    return final_graph

def main():
    # You can easily swap these for argparse if you want to pass paths via CLI
    input_path = "../data/timeseriessample.ttl"
    output_path = "../data/TSSgraph.ttl"

    print("--- Program Started ---")
    
    # 1. Load data
    original_graph = load_graph(input_path)
    
    # 2. Extract unique sensors
    sensor_set = create_sensor_set(original_graph)
    
    # 3. Process into TSS format
    tss_graph = create_tss(sensor_set, original_graph)
    
    # 4. Save result
    save_graph(output_path, tss_graph)
    
    print("--- Program Finished Successfully ---")

if __name__ == "__main__":
    main()