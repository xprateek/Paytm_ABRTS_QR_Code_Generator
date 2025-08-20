import json
import base64
import sys

AID = "77a7aa36c00e469482a6219004fde717"
MERCHANT_CITY_KEY = "ahmedabad_brts"
PATH = "/city-bus/getSourceDetails"

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

def main():
    try:
        source_id = input('Enter SOURCE_ID (e.g., "0092"): ').strip()
        if not source_id:
            print(json.dumps({
                "error": "SOURCE_ID is required. Please run again and provide a non-empty SOURCE_ID."
            }, indent=4))
            sys.exit(1)

        station_name = input('Enter BUS_STATION_NAME (e.g., "R.T.O Circle"): ').strip()
        if not station_name:
            station_name = "Unnamed Station"

        deeplink = build_deeplink(source_id)

        pretty_output = {
            "name": station_name,
            "text": deeplink,
            "size": 512,
            "ecl": "Q"
        }
        print("\n" + json.dumps(pretty_output, indent=4))
    except KeyboardInterrupt:
        # Graceful exit on Ctrl+C
        print("\nOperation cancelled.")
        sys.exit(1)

if __name__ == "__main__":
    main()
