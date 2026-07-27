def generate_timeseries_mapping(target_file_path):
    timeseries_mapping = f"""
@base <http://example.com/observations/> .
@prefix rr:    <http://www.w3.org/ns/r2rml#> .
@prefix rml:   <http://semweb.mmlab.be/ns/rml#> .
@prefix ql:    <http://semweb.mmlab.be/ns/ql#> .
@prefix sosa:  <http://www.w3.org/ns/sosa/> .
@prefix ssn:   <http://www.w3.org/ns/ssn/> .
@prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .
@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex:    <http://example.com/attributes/> .
@prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix obs:   <http://example.com/observations/> .
@prefix waterinfo: <http://example.com/waterinfo/> .
@prefix qudt:  <http://qudt.org/schema/qudt/> .
@prefix unit:  <http://qudt.org/vocab/unit/> .
@prefix quantitykind: <https://qudt.org/vocab/quantitykind/> .


<#SensorMapping> a rr:TriplesMap;
  rml:logicalSource [
    rml:source "../data/{target_file_path}.csv";
    rml:referenceFormulation ql:CSV
  ];

  # Core Subject Map
  rr:subjectMap [
    rr:template "111111111/{{DateTime}}" ;
    rr:class sosa:Observation
  ];

  # Sensor / ts_id
  rr:predicateObjectMap [
    rr:predicate sosa:madeBySensor ;
    rr:objectMap [
        rr:template "http://example.com/waterlink/111111111" ;
        rr:termType rr:IRI
    ]
  ] ;

  # Timestamp -> sosa:resultTime
  rr:predicateObjectMap [
    rr:predicate sosa:resultTime ;
    rr:objectMap [
      rml:reference "DateTime" ;
      rr:datatype xsd:dateTime
    ]
  ] ;

  # Value -> sosa:hasSimpleResult
  rr:predicateObjectMap [
    rr:predicate sosa:hasSimpleResult ;
    rr:objectMap [
      rml:reference "Conductivity dokwater + spui ABF | ZHINDS10_WINCC_INDUSS_02_AT9103-B_FEED_CONDUCTIVITY | µs/cm" ;
      rr:datatype xsd:double
    ]
  ] ;

  # Observed Property -> New Constant IRI
  rr:predicateObjectMap [
    rr:predicate sosa:observedProperty ;
    rr:objectMap [
      rr:constant quantitykind:ElectricConductivity ;
      rr:termType rr:IRI
    ]
  ] ;
  
# Unit of Measurement -> New Constant IRI
  rr:predicateObjectMap [
    rr:predicate qudt:hasUnit ;
    rr:objectMap [
      rr:constant unit:MicroS-PER-CentiM ;
      rr:termType rr:IRI
    ]
  ]
  .

"""
    
    print(f"Generated RML mapping for {target_file_path}.csv")

    # FIX: Explicitly add encoding="utf-8" here
    with open(f"../RML_mapping/{target_file_path}.rml.ttl", "w", encoding="utf-8") as f:
        f.write(timeseries_mapping)

    print(f"RML mapping saved to ../RML_mapping/{target_file_path}.rml.ttl")