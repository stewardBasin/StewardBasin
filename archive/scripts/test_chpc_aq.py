import os
import json
import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

FIXED_URL = "https://utahaq.chpc.utah.edu/jsondata/FixedSiteMapData.json"
MOBILE_URL = "https://utahaq.chpc.utah.edu/jsondata/MobileMapData.json"

os.makedirs(DATA_DIR, exist_ok=True)

def fetch_and_save(url, filename):
    print(f"\nFetching {url}")
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    data = response.json()

    output_path = os.path.join(DATA_DIR, filename)

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)

    print(f"Saved: {output_path}")

    if isinstance(data, list):
        print(f"Records: {len(data)}")
        if data:
            print("First record keys:")
            print(list(data[0].keys()))
            print("\nFirst record sample:")
            print(json.dumps(data[0], indent=2)[:1500])

    elif isinstance(data, dict):
        print("Top-level keys:")
        print(list(data.keys()))
        print("\nSample:")
        print(json.dumps(data, indent=2)[:1500])

def main():
    fetch_and_save(FIXED_URL, "chpc_fixed_site_map_data.json")
    fetch_and_save(MOBILE_URL, "chpc_mobile_map_data.json")

if __name__ == "__main__":
    main()