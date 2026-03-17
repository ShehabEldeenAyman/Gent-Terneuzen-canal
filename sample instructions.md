java -jar rmlmapper.jar -m mapping.rml.ttl -o linkeddata.ttl -s turtle

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