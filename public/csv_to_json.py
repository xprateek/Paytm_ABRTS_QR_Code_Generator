import csv
import json
from pathlib import Path

INPUT_CSV = "abrts_deeplinks.csv"
OUTPUT_JSON = "abrts_deeplinks.json"

DEFAULT_SIZE = 256
DEFAULT_ECL = "L"

def row_to_object(row: dict) -> dict:
    # Extract fields safely
    name = (row.get("BUS_STATION_NAME") or "").strip()
    if not name:
        name = "Unnamed Station"

    deeplink = (row.get("DEEPLINK") or "").strip()
    return {
        "name": name,
        "text": deeplink,
        "size": DEFAULT_SIZE,
        "ecl": DEFAULT_ECL
    }

def main():
    input_path = Path(INPUT_CSV)
    if not input_path.exists():
        raise FileNotFoundError(f"CSV not found: {input_path.resolve()}")

    items = []
    with input_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        # Expecting columns: SOURCE_ID, BUS_STATION_NAME, DEEPLINK
        for row in reader:
            # Skip rows with empty deeplink
            if not (row.get("DEEPLINK") or "").strip():
                continue
            items.append(row_to_object(row))

    # Write pretty JSON array
    with open(OUTPUT_JSON, "w", encoding="utf-8") as out:
        json.dump(items, out, ensure_ascii=False, indent=4)

    print(f"Wrote {len(items)} records to {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
