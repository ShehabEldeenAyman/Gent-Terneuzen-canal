from rdflib import Graph, Namespace, URIRef, Literal

def transform_unit(graph_directory, NEW_UNIT):
    g = Graph()
    
    # Define your namespaces to match the data
    QUDT = Namespace("http://qudt.org/schema/qudt/")
    SOSA = Namespace("http://www.w3.org/ns/sosa/")
    
    try:
        g.parse(graph_directory, format="turtle")
        print(f"Successfully loaded {len(g)} triples.\n")
        
        for subject in set(g.subjects()):
            # FIX 1: Look for QUDT.hasUnit instead of QUDT.unit
            unit_value = g.value(subject, QUDT.hasUnit)
            
            if unit_value is not None:
                print(f"Subject: {subject}")
                print(f"  └── Found target value: {unit_value}")
                temporary_graph = Graph()
                temporary_graph.parse(URIRef(unit_value))
                
                mult = temporary_graph.value(unit_value, QUDT.conversionMultiplier)
                off = temporary_graph.value(unit_value, QUDT.conversionOffset)
                conversion_multiplier = float(mult) if mult is not None else 1.0
                conversion_offset = float(off) if off is not None else 0.0
                print(f"  └── Found conversion multiplier value: {conversion_multiplier}")
                print(f"  └── Found conversion offset value: {conversion_offset}")
                
                for predicate, obj in g.predicate_objects(subject):
                    # FIX 2: Look for SOSA.hasSimpleResult instead of QUDT.value
                    if (predicate == SOSA.hasSimpleResult):
                        print(f"     ├── Predicate: {predicate}")
                        print(f"     └── Object:    {obj}")
                        
                        new_value = (float(obj) + conversion_offset) * conversion_multiplier
                        
                        print(f"     ├── converted value: {new_value}")
                        print(f"     ├── new unit: {NEW_UNIT}")
                        
                        # FIX 3: Update the correct predicates when saving
                        g.set((subject, SOSA.hasSimpleResult, Literal(new_value)))
                        g.set((subject, QUDT.hasUnit, NEW_UNIT))
                        
                        g.serialize(destination=graph_directory, format="turtle")
                        print(f"\nMeasuring Unit Transformed! graph saved to {graph_directory}")
    except Exception as e:
            print(f"Error parsing the file: {e}")

def transform_unit_optimized(graph_directory, NEW_UNIT):
    g = Graph()
    
    QUDT = Namespace("http://qudt.org/schema/qudt/")
    SOSA = Namespace("http://www.w3.org/ns/sosa/")
    
    # Dict handles multiple distinct units dynamically as they appear
    unit_cache = {}
    
    try:
        g.parse(graph_directory, format="turtle")
        print(f"Successfully loaded {len(g)} triples.\n")
        
        graph_modified = False 
        
        for subject in set(g.subjects()):
            unit_value = g.value(subject, QUDT.hasUnit)
            
            if unit_value is not None:
                
                # SMART CHECK: If the element is already in the target unit, skip it!
                if unit_value == NEW_UNIT:
                    continue
                
                # DYNAMIC CACHING: If it's a unit we haven't seen yet, look it up and cache it
                if unit_value not in unit_cache:
                    print(f"Network Request: Fetching conversion data for new unit '{unit_value}'...")
                    temporary_graph = Graph()
                    temporary_graph.parse(str(unit_value)) 
                    
                    mult = temporary_graph.value(unit_value, QUDT.conversionMultiplier)
                    off = temporary_graph.value(unit_value, QUDT.conversionOffset)
                    
                    conversion_multiplier = float(mult) if mult is not None else 1.0
                    conversion_offset = float(off) if off is not None else 0.0
                    
                    # Store it so any future elements with this unit reuse it
                    unit_cache[unit_value] = (conversion_multiplier, conversion_offset)
                    print(f"  └── Cached multiplier: {conversion_multiplier}, offset: {conversion_offset}")
                else:
                    # Instant hit if we've seen this unit type earlier in the loop
                    conversion_multiplier, conversion_offset = unit_cache[unit_value]

                # --- VALUE UPDATE LOGIC ---
                for predicate, obj in g.predicate_objects(subject):
                    if (predicate == SOSA.hasSimpleResult):
                        new_value = (float(obj) + conversion_offset) * conversion_multiplier
                        
                        g.set((subject, SOSA.hasSimpleResult, Literal(new_value)))
                        g.set((subject, QUDT.hasUnit, NEW_UNIT))
                        
                        graph_modified = True
                        
        if graph_modified:
            g.serialize(destination=graph_directory, format="turtle")
            print(f"\nOptimization complete! Graph saved to {graph_directory}")
        else:
            print("\nNo transformations needed. All elements already match the target unit.")
            
    except Exception as e:
            print(f"Error processing the file: {e}")

def main():
    transform_unit_optimized("../data/water_link.ttl", URIRef("http://qudt.org/vocab/unit/MilliS-PER-CentiM"))

if __name__ == "__main__":
    main()