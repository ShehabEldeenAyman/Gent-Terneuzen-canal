#VIRTUOSO_URL = "http://localhost:8890/sparql-graph-crud"
VIRTUOSO_URL = "http://localhost:8890/sparql"
GRAPH_URI = "http://example.com/Gent-Terneuzen/conductivity"
USERNAME = "dba"
PASSWORD = "dba"
AUTH  = (USERNAME,PASSWORD)

params  = {'graph': GRAPH_URI}
headers = {'Accept': 'text/turtle'}

conductivity_stations = ["HIS_BWO_VITO_IOW50", "HIS_BWO_VITO_IOW48", "BWO_VITO_IOW49", "BWO_VITO_IOW51"]
conductivity_sensors = ['289441042','289435042', '289429042', '289423042' ] #arranged furthest to nearest
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
    'conductivity': conductivity_sensors,
    #'waterlevel': waterlevel_sensors
}


