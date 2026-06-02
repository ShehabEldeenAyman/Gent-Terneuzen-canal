java -jar rmlmapper.jar -m timeseriesmapping.rml.ttl -o timeseries.ttl -s turtle
java -jar rmlmapper.jar -m stationmapping.rml.ttl -o stations.ttl -s turtle

fastapi dev

npm run dev

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


python -c "import joblib; s=joblib.load('scaler_v2.pkl'); print(s.data_min_[0], s.data_max_[0])"   #extract scalar values

pm2 start npm --name "frontend" -- run dev -- --host

pm2 list (See what's running)
pm2 logs (See the console output)
pm2 stop my-app (Stop the process)