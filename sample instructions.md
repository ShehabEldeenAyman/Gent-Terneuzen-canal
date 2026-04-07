java -jar rmlmapper.jar -m timeseriesmapping.rml.ttl -o timeseries.ttl -s turtle
java -jar rmlmapper.jar -m stationmapping.rml.ttl -o stations.ttl -s turtle

fastapi dev


PREFIX sosa: <http://www.w3.org/ns/sosa/>
SELECT ?observation ?time ?value
FROM <http://example.com/Gent-Terneuzen>
WHERE {
  ?observation a sosa:Observation ;
               sosa:resultTime ?time ;
               sosa:hasSimpleResult ?value .
}
LIMIT 10

SELECT (COUNT(*) AS ?totalTriples)
FROM <http://example.com/Gent-Terneuzen>
WHERE {
  ?s ?p ?o .
}

DROP GRAPH <http://example.com/Gent-Terneuzen> ;