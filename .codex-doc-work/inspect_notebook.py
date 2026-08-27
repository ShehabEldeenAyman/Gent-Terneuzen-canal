import json
import re
import sys
from pathlib import Path


def main() -> None:
    path = Path(sys.argv[1])
    terms = [term.casefold() for term in sys.argv[2:]]
    notebook = json.loads(path.read_text(encoding="utf-8"))
    print(f"FILE: {path}")
    for index, cell in enumerate(notebook.get("cells", [])):
        source = "".join(cell.get("source", []))
        if not source.strip():
            continue
        folded = source.casefold()
        if terms and not any(term in folded for term in terms):
            continue
        compact = re.sub(r"[ \t]+", " ", source).strip()
        print(f"\nCELL {index} [{cell.get('cell_type')}]\n{compact}")


if __name__ == "__main__":
    main()
