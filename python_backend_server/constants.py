#VIRTUOSO_URL = "http://localhost:8890/sparql-graph-crud"
VIRTUOSO_URL = "http://localhost:8890/sparql"
GRAPH_URI = "http://example.com/Gent-Terneuzen/conductivity"
USERNAME = "dba"
PASSWORD = "dba"
AUTH  = (USERNAME,PASSWORD)

params  = {'graph': GRAPH_URI}
headers = {'Accept': 'text/turtle'}

water_info_conductivity_stations = ["HIS_BWO_VITO_IOW50", "HIS_BWO_VITO_IOW48", "BWO_VITO_IOW49", "BWO_VITO_IOW51"]
water_info_conductivity_sensors = ['289441042','289435042', '289429042', '289423042' ] #arranged furthest to nearest
#289441042 -> Terneuzen
#289435042 -> Westdorpe
#289429042 -> Gent - far
#289423042 -> Gent - near

water_link_conductivity_sensor = ['111111111'] #At the Indusii site

waterlevel_stations = ["kgt04a-1066"]
waterlevel_sensors = ['98524010']



colors  = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']

target_sensor = '289441042'

################################################################
data_dictionary = {
    'water_info': water_info_conductivity_sensors,
    #'waterlevel': waterlevel_sensors
}


TSS_GRAPH_URI = "http://example.com/Gent-Terneuzen-TSS"
    
TIMESERIES_TTL = "../data/timeseries.ttl"
STATIONS_TTL = "../data/stations.ttl"
TSS_GRAPH_TTL = "../data/TSSgraph.ttl"

START_DATE = "2025-01-01T00:00:00Z"
TEST_END_DATE = "2021-05-30T00:00:00Z"
END_DATE = "2025-12-31T23:59:59Z"