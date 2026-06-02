import os
import json
import re
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN_DIR = os.path.join(BASE_DIR, "clean")
DATA_DIR = os.path.join(BASE_DIR, "data")

os.makedirs(DATA_DIR, exist_ok=True)

INPUT_FILES = [
    "promoted_keep.json",
    "promoted_maybe.json",
    "clean_complaints.json",
    "clean_h2s.json",
    "clean_operations.json",
    "clean_spills.json",
    "needs_review_industrial.json",
]

MIN_YEAR = 2016

# Approximate community / project locations.
# These are intentionally transparent and conservative.
PLACE_LOOKUP = [
    {
        "label": "Blue Bench / Roosevelt industrial area",
        "keywords": ["blue bench", "4-c farms", "iwm mine", "blue bench gravel", "blue bench landfill"],
        "lat": 40.327,
        "lng": -110.074,
        "confidence": "approximate_known_facility_area",
    },
    {
        "label": "Lamb Road / Higley area",
        "keywords": ["lamb road", "higley"],
        "lat": 40.28,
        "lng": -110.05,
        "confidence": "approximate_named_area",
    },
    {
        "label": "Pleasant Valley / 4500 West and 10000 South",
        "keywords": ["pleasant valley", "4500 west", "10000 south"],
        "lat": 40.094,
        "lng": -110.087,
        "confidence": "approximate_named_intersection",
    },
    {
        "label": "River Road / Duchesne River corridor",
        "keywords": ["river road", "duchesne river", "along the river road"],
        "lat": 40.181,
        "lng": -110.37,
        "confidence": "approximate_named_corridor",
    },
    {
        "label": "Wells Draw area",
        "keywords": ["wells draw"],
        "lat": 40.20,
        "lng": -110.30,
        "confidence": "approximate_named_area",
    },
    {
        "label": "Duchesne City area",
        "keywords": ["duchesne city", "duchesne area", "duchesne county"],
        "lat": 40.1633,
        "lng": -110.4029,
        "confidence": "community_level",
    },
    {
        "label": "Roosevelt area",
        "keywords": ["roosevelt"],
        "lat": 40.2994,
        "lng": -109.9887,
        "confidence": "community_level",
    },
    {
        "label": "Myton area",
        "keywords": ["myton"],
        "lat": 40.1944,
        "lng": -110.0618,
        "confidence": "community_level",
    },
    {
        "label": "Bluebell area",
        "keywords": ["bluebell"],
        "lat": 40.359,
        "lng": -110.21,
        "confidence": "community_level",
    },
    {
        "label": "Tabiona area",
        "keywords": ["tabiona"],
        "lat": 40.3549,
        "lng": -110.7071,
        "confidence": "community_level",
    },
    {
        "label": "Fruitland area",
        "keywords": ["fruitland"],
        "lat": 40.2144,
        "lng": -110.8413,
        "confidence": "community_level",
    },
    {
        "label": "Fort Duchesne area",
        "keywords": ["fort duchesne"],
        "lat": 40.2889,
        "lng": -109.8618,
        "confidence": "community_level",
    },
    {
        "label": "Horsepool area",
        "keywords": ["horsepool"],
        "lat": 40.143,
        "lng": -109.468,
        "confidence": "community_level",
    },
    {
        "label": "South Ouray area",
        "keywords": ["south ouray", "ouray"],
        "lat": 40.0894,
        "lng": -109.6812,
        "confidence": "community_level",
    },
]

CATEGORY_RULES = {
    "dust_complaints.json": {
        "type": "Dust / PM10 Complaint",
        "category": "Dust / PM10",
        "keywords": [
            "dust", "pm10", "pm 10", "pm2.5", "particulate",
            "gravel pit", "sand pit", "sand mine", "rock crusher",
            "crusher", "quarry", "haul road", "haul route",
            "truck traffic", "trucks", "fugitive dust"
        ],
        "must_not": ["air conservation act", "state statute", "utah code annotated"],
    },
    "h2s_odor_complaints.json": {
        "type": "H2S / Odor Complaint",
        "category": "H2S / Odor",
        "keywords": [
            "h2s", "h₂s", "hydrogen sulfide", "odor", "odour",
            "smell", "rotten egg", "gas smell"
        ],
        "must_not": [],
    },
    "noise_flaring_complaints.json": {
        "type": "Noise / Flaring Complaint",
        "category": "Noise / Flaring",
        "keywords": [
            "flare", "flaring", "compressor", "noise", "vibration",
            "decibel", "db", "hertz", "whistle"
        ],
        "must_not": [],
    },
    "oil_gas_incident_candidates.json": {
        "type": "Oil & Gas Incident / Operations Concern",
        "category": "Oil & Gas Incident Candidate",
        "keywords": [
            "spill", "release", "incident", "blowout", "leak",
            "produced water", "tank battery", "pipeline", "well pad",
            "drilling", "injection", "reserve pit", "oilfield waste"
        ],
        "must_not": [],
    },
    "industrial_operations_candidates.json": {
        "type": "Industrial Operation / Facility Concern",
        "category": "Industrial Operation",
        "keywords": [
            "conditional use permit", "cup", "mine", "landfill",
            "processing site", "industrial", "sand and gravel",
            "gravel extraction", "quarry", "crusher"
        ],
        "must_not": [],
    },
}

def load_json(path):
    try:
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            return []
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, list) else [data]
    except json.JSONDecodeError as error:
        print(f"Skipping invalid JSON: {path} — {error}")
        return []

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)

def collect_text(record):
    parts = []

    def add(value):
        if value is None:
            return
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, (int, float)):
            parts.append(str(value))
        elif isinstance(value, list):
            for item in value:
                add(item)
        elif isinstance(value, dict):
            for v in value.values():
                add(v)

    add(record)
    return " ".join(parts)

def get_year(record, text):
    for key in ["year", "date", "date_found", "meeting_date", "created_at"]:
        value = record.get(key)
        if value:
            match = re.search(r"(19|20)\d{2}", str(value))
            if match:
                return int(match.group(0))

    match = re.search(r"(19|20)\d{2}", text)
    if match:
        return int(match.group(0))

    return None

def find_place(text_lower):
    for place in PLACE_LOOKUP:
        if any(keyword in text_lower for keyword in place["keywords"]):
            return place
    return None

def existing_coords(record):
    lat = record.get("lat")
    lng = record.get("lng")

    if lat not in [None, "", "--"] and lng not in [None, "", "--"]:
        try:
            return float(lat), float(lng), "existing_coordinates"
        except ValueError:
            return None

    return None

def first_snippet(record, text):
    for key in ["description", "snippet", "summary", "text"]:
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()[:850]

    matches = record.get("matches")
    if isinstance(matches, list):
        for match in matches:
            if isinstance(match, dict) and match.get("snippet"):
                return match["snippet"].strip()[:850]

    return text.strip()[:850]

def rule_matches(rule, text_lower):
    if any(blocked in text_lower for blocked in rule.get("must_not", [])):
        return False
    return any(keyword in text_lower for keyword in rule["keywords"])

def make_record(original, source_file, rule, text, year, place):
    coords = existing_coords(original)

    if coords:
        lat, lng, confidence = coords
        label = original.get("location_label", "")
        map_ready = True
    elif place:
        lat = place["lat"]
        lng = place["lng"]
        confidence = place["confidence"]
        label = place["label"]
        map_ready = True
    else:
        lat = ""
        lng = ""
        confidence = "needs_location_review"
        label = ""
        map_ready = False

    date_value = original.get("date") or original.get("date_found") or str(year or "")

    return {
        "id": original.get("id") or original.get("source_file") or source_file,
        "type": original.get("type") or rule["type"],
        "description": first_snippet(original, text),
        "date": date_value,
        "year": str(year or ""),
        "county": original.get("county") or "Duchesne",
        "source": original.get("source") or "Parsed public record",
        "source_file": original.get("source_file") or source_file,
        "category": rule["category"],
        "industry": original.get("industry") or "",
        "lat": lat,
        "lng": lng,
        "location_label": label,
        "location_confidence": confidence,
        "map_ready": map_ready,
        "review_status": "map_ready" if map_ready else "needs_location",
        "source_clean_file": source_file,
        "promoted_at": datetime.now().isoformat(),
    }

def dedupe(records):
    seen = set()
    output = []

    for record in records:
        key = (
            record.get("source_file", ""),
            record.get("category", ""),
            record.get("description", "")[:140],
            str(record.get("lat", "")),
            str(record.get("lng", "")),
        )

        if key in seen:
            continue

        seen.add(key)
        output.append(record)

    return output

def main():
    outputs = {filename: [] for filename in CATEGORY_RULES}
    needs_location = []

    total_seen = 0
    total_modern = 0

    for source_file in INPUT_FILES:
        path = os.path.join(CLEAN_DIR, source_file)
        records = load_json(path)

        for original in records:
            if not isinstance(original, dict):
                continue

            total_seen += 1

            text = collect_text(original)
            text_lower = text.lower()
            year = get_year(original, text)

            if year is None or year < MIN_YEAR:
                continue

            total_modern += 1
            place = find_place(text_lower)

            matched_any = False

            for filename, rule in CATEGORY_RULES.items():
                if rule_matches(rule, text_lower):
                    promoted = make_record(
                        original=original,
                        source_file=source_file,
                        rule=rule,
                        text=text,
                        year=year,
                        place=place,
                    )

                    outputs[filename].append(promoted)
                    matched_any = True

                    if not promoted["map_ready"]:
                        needs_location.append(promoted)

            if not matched_any:
                continue

    print("\n==============================")
    print("STEWARD BASIN MAP PROMOTION")
    print("==============================")
    print(f"Total source records checked: {total_seen}")
    print(f"2016+ records checked:        {total_modern}")

    for filename, records in outputs.items():
        cleaned = dedupe(records)
        output_path = os.path.join(DATA_DIR, filename)
        save_json(output_path, cleaned)

        ready = sum(1 for r in cleaned if r["map_ready"])
        print(f"{filename}: {len(cleaned)} records | map-ready: {ready}")

    needs_location = dedupe(needs_location)
    save_json(os.path.join(DATA_DIR, "needs_location_review.json"), needs_location)
    print(f"needs_location_review.json: {len(needs_location)}")

    print("\nDone. New map-layer candidate files saved in:")
    print(DATA_DIR)

if __name__ == "__main__":
    main()