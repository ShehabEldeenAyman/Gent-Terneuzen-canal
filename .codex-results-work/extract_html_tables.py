import io
import json
import sys
from pathlib import Path

import pandas as pd


def flatten(value):
    if isinstance(value, list):
        return "".join(str(item) for item in value)
    return str(value)


def main() -> None:
    path = Path(sys.argv[1])
    cell_index = int(sys.argv[2])
    output_index = int(sys.argv[3])
    notebook = json.loads(path.read_text(encoding="utf-8"))
    output = notebook["cells"][cell_index]["outputs"][output_index]
    html = flatten(output.get("data", {}).get("text/html", ""))
    if not html:
        raise SystemExit("Selected output has no text/html")
    tables = pd.read_html(io.StringIO(html))
    for table_index, table in enumerate(tables):
        print(f"TABLE {table_index} shape={table.shape}")
        if isinstance(table.columns, pd.MultiIndex):
            table.columns = [
                " | ".join(str(value) for value in column if not str(value).startswith("Unnamed"))
                for column in table.columns
            ]
        print(table.to_csv(index=False))


if __name__ == "__main__":
    main()
