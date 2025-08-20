import json
import base64
import csv

AID = "77a7aa36c00e469482a6219004fde717"
MERCHANT_CITY_KEY = "ahmedabad_brts"
PATH = "/city-bus/getSourceDetails"
OUTPUT_CSV = "abrts_deeplinks.csv"

def build_deeplink(source_id: str) -> str:
    payload = {
        "path": PATH,
        "params": {
            "merchantCityKey": MERCHANT_CITY_KEY,
            "sourceId": source_id
        },
        "sparams": {
            "pullRefresh": False,
            "canPullDown": False,
            "showTitleBar": False
        }
    }
    json_str = json.dumps(payload, separators=(',', ':'))
    b64 = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
    return f"paytmmp://mini-app?aId={AID}&data={b64}"

def station_name_for(source_id: str) -> str:
    # Customize this mapping as needed. For now: generic name per ID.
    # Example for custom names:
    # names = {"0001": "R.T.O Circle", "0002": "Some Stop", ...}
    # return names.get(source_id, f"Station {source_id}")
    return f"Station {source_id}"

def main():
    start = 1
    end = 210

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["SOURCE_ID", "BUS_STATION_NAME", "DEEPLINK"])

        for i in range(start, end + 1):
            source_id = f"{i:04d}"  # zero-padded 4 digits
            name = station_name_for(source_id)
            deeplink = build_deeplink(source_id)
            writer.writerow([source_id, name, deeplink])

    print(f"CSV generated: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
