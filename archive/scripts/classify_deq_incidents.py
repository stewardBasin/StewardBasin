import os
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

INPUT_FILE = os.path.join(DATA_DIR, "deq_incidents.json")
OUTPUT_FILE = os.path.join(DATA_DIR, "deq_incidents_classified.json")


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def combined_text(record):
    raw = record.get("raw_record", {}) or {}

    parts = [
        record.get("type", ""),
        record.get("description", ""),
        record.get("company", ""),
        record.get("material", ""),
        raw.get("name", ""),
        raw.get("title_eventname", ""),
        raw.get("incident_summary", ""),
        raw.get("responsible_party", ""),
        raw.get("address", ""),
        raw.get("city", ""),
        raw.get("nearest_city", ""),
    ]

    return " ".join(str(part) for part in parts if part).lower()


def classify_incident(record):
    text = combined_text(record)

    if "h2s" in text or "hydrogen sulfide" in text:
        return "H2S Release"

    if (
        "treated injection water" in text
        or "produced water" in text
        or "production water" in text
        or "brine" in text
        or "salt water" in text
        or "saltwater" in text
    ):
        return "Produced Water Release"

    if "mercury" in text:
        return "Mercury Incident"

    if "hydraulic oil" in text:
        return "Hydraulic Oil Leak"

    if (
        "crude oil" in text
        or "condensate" in text
        or "oil spill" in text
        or "barrels of oil" in text
        or "bbls of oil" in text
    ):
        return "Oil Spill"

    if "diesel" in text or "gasoline" in text or "fuel" in text or "jet fuel" in text:
        return "Fuel Spill"

    if (
        "sewage" in text
        or "wastewater" in text
        or "waste water" in text
        or "sewer" in text
    ):
        return "Wastewater Release"

    if (
        "chemical" in text
        or "acid" in text
        or "solvent" in text
        or "chlorine" in text
        or "pesticide" in text
        or "herbicide" in text
    ):
        return "Chemical Release"

    return "Unknown Incident"


def get_display_date(record):
    raw = record.get("raw_record", {}) or {}

    return (
        record.get("date")
        or raw.get("date_discovered")
        or raw.get("date_discovered_for_filter")
        or ""
    )


def get_display_description(record):
    raw = record.get("raw_record", {}) or {}

    return (
        raw.get("incident_summary")
        or record.get("description")
        or raw.get("title_eventname")
        or raw.get("name")
        or "Environmental incident reported to Utah DEQ."
    )


def main():
    records = load_json(INPUT_FILE)
    output = []

    for record in records:
        raw = record.get("raw_record", {}) or {}

        incident_type = classify_incident(record)

        cleaned = {
            "id": record.get("id") or raw.get("derrid") or raw.get("id"),
            "type": incident_type,
            "date": get_display_date(record),
            "county": record.get("county", ""),
            "company": record.get("company") or raw.get("responsible_party", ""),
            "material": record.get("material", ""),
            "description": get_display_description(record),
            "lat": record.get("lat"),
            "lng": record.get("lng"),
            "nearest_city": raw.get("nearest_city") or raw.get("city", ""),
            "address": raw.get("address") or raw.get("address_location", ""),
            "title": raw.get("title_eventname") or raw.get("name", ""),
            "source": "Utah DEQ Environmental Incident Database",
            "source_url": record.get("source_url", ""),
            "category": "DEQ Environmental Incident",
            "location_confidence": record.get(
                "location_confidence", "reported_coordinates"
            ),
            "map_ready": record.get("map_ready", True),
            "raw_record": raw,
            "classified_at": datetime.now().isoformat(),
        }

        output.append(cleaned)

    save_json(OUTPUT_FILE, output)

    counts = {}
    for record in output:
        counts[record["type"]] = counts.get(record["type"], 0) + 1

    print("\n==============================")
    print("DEQ INCIDENTS CLASSIFIED")
    print("==============================")
    print(f"Input records:  {len(records)}")
    print(f"Output records: {len(output)}")
    print(f"Saved: {OUTPUT_FILE}")
    print("\nCounts by type:")

    for key in sorted(counts):
        print(f"{key}: {counts[key]}")


if __name__ == "__main__":
    main()
