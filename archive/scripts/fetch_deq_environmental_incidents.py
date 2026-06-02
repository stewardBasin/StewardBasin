import os
import json
import re
import requests
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

SOURCE_URL = "https://opendata.utah.gov/resource/sce7-b7au.json"

OUTPUT_RAW_ALL = os.path.join(DATA_DIR, "deq_environmental_incidents_all.json")
OUTPUT_RAW_BASIN = os.path.join(DATA_DIR, "deq_environmental_incidents_basin.json")
OUTPUT_MAP_READY = os.path.join(DATA_DIR, "deq_incidents.json")
OUTPUT_NEEDS_LOCATION = os.path.join(DATA_DIR, "deq_incidents_needs_location.json")

BASIN_COUNTIES = {"DUCHESNE", "UINTAH"}


def fetch_records():
    params = {"$limit": 50000}
    response = requests.get(SOURCE_URL, params=params, timeout=90)
    response.raise_for_status()
    return response.json()


def clean(value):
    if value is None:
        return ""
    return str(value).strip()


def get_field(record, possible_names):
    lower_record = {k.lower(): v for k, v in record.items()}
    for name in possible_names:
        value = lower_record.get(name.lower())
        if value not in [None, "", "--"]:
            return value
    return ""


def get_county(record):
    return clean(get_field(record, ["county", "county_name"])).upper()


def get_lat_lng(record):
    # 1. Socrata geometry field
    geom = record.get("the_geom")

    if isinstance(geom, dict):
        coords = geom.get("coordinates")

        if isinstance(coords, list) and len(coords) >= 2:
            try:
                lng = float(coords[0])
                lat = float(coords[1])
                return lat, lng
            except ValueError:
                pass

    # 2. Sometimes geometry may be a string
    if isinstance(geom, str):
        match = re.search(r"-?\d+\.\d+", geom)
        numbers = re.findall(r"-?\d+\.\d+", geom)

        if len(numbers) >= 2:
            try:
                lng = float(numbers[0])
                lat = float(numbers[1])
                return lat, lng
            except ValueError:
                pass

    # 3. Fallback to normal latitude / longitude fields
    lat = get_field(record, ["latitude", "lat", "y"])
    lng = get_field(record, ["longitude", "lon", "lng", "x"])

    if lat and lng:
        try:
            return float(lat), float(lng)
        except ValueError:
            pass

    return "", ""


def classify_incident(material, description):
    text = f"{material} {description}".lower()

    if "h2s" in text or "hydrogen sulfide" in text:
        return "H2S / Gas Release"
    if "produced water" in text or "production water" in text or "brine" in text:
        return "Produced Water Release"
    if "crude" in text or "oil" in text or "condensate" in text:
        return "Oil / Condensate Spill"
    if "diesel" in text or "fuel" in text or "gasoline" in text:
        return "Fuel Spill"
    if "sewage" in text or "wastewater" in text:
        return "Wastewater Release"
    if "chemical" in text:
        return "Chemical Release"

    return "Environmental Incident"


def normalize_record(record, index):
    report_number = get_field(
        record,
        ["report_number", "report_no", "incident_number", "incident_id", "case_number"],
    )

    date = get_field(
        record,
        ["date_reported", "reported_date", "date", "incident_date", "date_received"],
    )

    company = get_field(
        record,
        [
            "company",
            "responsible_party",
            "responsible_company",
            "organization",
            "facility",
        ],
    )

    material = get_field(
        record, ["material_chem", "material", "chemical", "substance", "product"]
    )

    description = get_field(
        record,
        [
            "description",
            "incident_description",
            "comments",
            "narrative",
            "location_description",
        ],
    )

    county = get_county(record)
    lat, lng = get_lat_lng(record)

    incident_type = classify_incident(material, description)

    return {
        "id": report_number or f"deq_incident_{index}",
        "type": incident_type,
        "date": clean(date),
        "county": county.title(),
        "company": clean(company),
        "material": clean(material),
        "description": clean(description) or f"{incident_type} reported to Utah DEQ.",
        "lat": lat,
        "lng": lng,
        "source": "Utah DEQ Environmental Incident Database",
        "source_url": SOURCE_URL,
        "category": "DEQ Environmental Incident",
        "location_confidence": (
            "reported_coordinates" if lat and lng else "needs_location_review"
        ),
        "map_ready": bool(lat and lng),
        "raw_record": record,
    }


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def main():
    records = fetch_records()

    basin_raw = [record for record in records if get_county(record) in BASIN_COUNTIES]

    normalized = [
        normalize_record(record, index)
        for index, record in enumerate(basin_raw, start=1)
    ]

    map_ready = [record for record in normalized if record["map_ready"]]
    needs_location = [record for record in normalized if not record["map_ready"]]

    save_json(OUTPUT_RAW_ALL, records)
    save_json(OUTPUT_RAW_BASIN, basin_raw)
    save_json(OUTPUT_MAP_READY, map_ready)
    save_json(OUTPUT_NEEDS_LOCATION, needs_location)

    print("\n==============================")
    print("DEQ ENVIRONMENTAL INCIDENTS")
    print("==============================")
    print(f"All Utah records:        {len(records)}")
    print(f"Duchesne/Uintah records: {len(basin_raw)}")
    print(f"Map-ready records:       {len(map_ready)}")
    print(f"Needs location review:   {len(needs_location)}")
    print(f"\nSaved map layer: {OUTPUT_MAP_READY}")

    if basin_raw:
        print("\nSample raw fields:")
        print(sorted(basin_raw[0].keys()))


if __name__ == "__main__":
    main()
