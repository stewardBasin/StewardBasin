import os
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN_DIR = os.path.join(BASE_DIR, "clean")
DATA_DIR = os.path.join(BASE_DIR, "data")

INPUT_FILE = os.path.join(CLEAN_DIR, "promoted_keep.json")
OUTPUT_FILE = os.path.join(DATA_DIR, "dust_complaints.json")

PLACE_LOOKUP = [
    {
        "name": "Pleasant Valley / 4500 West and 10000 South",
        "keywords": ["4500 west", "10000 south", "pleasant valley"],
        "lat": 40.094,
        "lng": -110.087,
        "confidence": "approximate",
    },
    {
        "name": "River Road / Duchesne River Corridor",
        "keywords": ["river road", "along the river"],
        "lat": 40.181,
        "lng": -110.37,
        "confidence": "approximate",
    },
    {
        "name": "Lamb Road / Higley sand haul route",
        "keywords": ["lamb road", "higley"],
        "lat": 40.28,
        "lng": -110.05,
        "confidence": "approximate",
    },
    {
        "name": "Hancock Cove",
        "keywords": ["hancock cove"],
        "lat": 40.18,
        "lng": -110.36,
        "confidence": "approximate",
    },
]

DUST_KEYWORDS = [
    "dust",
    "pm 10",
    "pm10",
    "particulate matter",
    "gravel pit",
    "sand and gravel",
    "crusher",
    "rock crusher",
    "asthma",
    "haul route",
    "trucks hauling sand",
]


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def combined_text(record):
    parts = [
        record.get("id", ""),
        record.get("category", ""),
        record.get("source_file", ""),
    ]

    for match in record.get("matches", []):
        parts.append(match.get("keyword", ""))
        parts.append(match.get("snippet", ""))

    return " ".join(parts).lower()


def find_place(text):
    for place in PLACE_LOOKUP:
        if any(keyword in text for keyword in place["keywords"]):
            return place

    return None


def is_dust_related(text):
    return any(keyword in text for keyword in DUST_KEYWORDS)


def make_description(record):
    snippets = [
        match.get("snippet", "").strip()
        for match in record.get("matches", [])
        if match.get("snippet")
    ]

    if snippets:
        return snippets[0][:650]

    return "Dust, PM10, gravel, mining, or industrial air-quality concern identified in source record."


def main():
    records = load_json(INPUT_FILE)
    output = []

    for record in records:
        text = combined_text(record)

        if not is_dust_related(text):
            continue

        place = find_place(text)

        mapped = {
            "id": record.get("id"),
            "type": "Dust / PM10 / Gravel Concern",
            "description": make_description(record),
            "date": record.get("date_found") or record.get("year") or "",
            "year": record.get("year", ""),
            "county": record.get("county", "Duchesne"),
            "source": "Parsed county record",
            "source_file": record.get("source_file", ""),
            "category": record.get("category", "Dust / PM10"),
            "industry": "Sand / Gravel / Industrial",
            "lat": place["lat"] if place else "",
            "lng": place["lng"] if place else "",
            "location_label": place["name"] if place else "",
            "location_confidence": place["confidence"] if place else "needs_location_review",
            "map_ready": bool(place),
            "review_status": "mapped_approximate" if place else "needs_location",
            "created_at": datetime.now().isoformat(),
        }

        output.append(mapped)

    save_json(OUTPUT_FILE, output)

    print("\n==============================")
    print("DUST COMPLAINTS PROMOTED")
    print("==============================")
    print(f"Input:  {INPUT_FILE}")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Records written: {len(output)}")
    print(f"Map-ready: {sum(1 for item in output if item['map_ready'])}")
    print(f"Needs location: {sum(1 for item in output if not item['map_ready'])}")


if __name__ == "__main__":
    main()