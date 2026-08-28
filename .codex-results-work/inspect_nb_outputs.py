import json
import sys
from pathlib import Path


def flatten(value):
    if isinstance(value, list):
        return "".join(str(item) for item in value)
    return str(value)


def main() -> None:
    path = Path(sys.argv[1])
    notebook = json.loads(path.read_text(encoding="utf-8"))
    print(f"FILE: {path}")
    for index, cell in enumerate(notebook.get("cells", [])):
        outputs = cell.get("outputs", [])
        if not outputs:
            continue
        source = flatten(cell.get("source", [])).strip().splitlines()
        label = source[0][:140] if source else ""
        print(f"\n=== CELL {index} ({cell.get('cell_type')}) {label} ===")
        for output_index, output in enumerate(outputs):
            output_type = output.get("output_type", "")
            print(f"--- OUTPUT {output_index} type={output_type} ---")
            if output_type == "stream":
                print(flatten(output.get("text", "")))
            elif output_type in {"execute_result", "display_data"}:
                data = output.get("data", {})
                for mime in ("text/plain", "text/markdown"):
                    if mime in data:
                        print(f"[{mime}]")
                        print(flatten(data[mime]))
            elif output_type == "error":
                print(output.get("ename"), output.get("evalue"))
                print("\n".join(output.get("traceback", [])))


if __name__ == "__main__":
    main()
