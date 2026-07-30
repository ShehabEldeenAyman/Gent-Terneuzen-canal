from pathlib import Path
import time

import pyshacl
import rdflib


def validate_shacl(data_location, shapes_location, report_name):
    data = rdflib.Graph().parse(data_location, format="turtle")
    shapes = rdflib.Graph().parse(shapes_location, format="turtle")
    started = time.perf_counter()
    conforms, _results_graph, results_text = pyshacl.validate(
        data, shacl_graph=shapes, advanced=True, abort_on_first=False, meta_shacl=False,
    )
    report_path = Path(report_name)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(results_text, encoding="utf-8")
    duration = round(time.perf_counter() - started, 2)
    message = "SHACL validation conforms." if conforms else "SHACL validation found violations."
    print(message)
    print(f"Report saved to {report_path}")
    return {"message": message, "conforms": conforms, "duration_seconds": duration}
