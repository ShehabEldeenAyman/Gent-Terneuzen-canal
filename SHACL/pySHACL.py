import time
import pyshacl
import rdflib

def validate_shacl(data_location,shapes_location,report_name):
    data = rdflib.Graph().parse(data_location, format="turtle")
    shapes = rdflib.Graph().parse(shapes_location, format="turtle")

    t0 = time.time()
    conforms, results_graph, results_text = pyshacl.validate(
    data,
    shacl_graph=shapes,
    advanced=True,          # required — you're using sh:sparql (SPARQLConstraintComponent)
    abort_on_first=False,   # set True to stop at the first violation, much faster for a quick check
    meta_shacl=False,
    )

    print("Conforms:", conforms)
    print("Took:", round(time.time() - t0, 1), "seconds")
    print(f"{shapes_location} SHACL report saved successfully")
    file = open(f"../data/{report_name}.txt", "w")
    file.write(results_text)
    file.close()
