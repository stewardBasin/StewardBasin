import json
import shutil
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

REVIEW_FILE = BASE_DIR / "data" / "verified_complaint_location_review.json"
COMPLAINTS_FILE = BASE_DIR / "data" / "complaints.json"

BACKUP_FILE = (
    BASE_DIR
    / "data"
    / f"complaints_before_county_fallback_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
)

COUNTY_FALLBACK = {
    "DUCHESNE": {
        "lat": 40.1633,
        "lng": -110.4029,
        "label": "Duchesne County - county-level complaint, no address provided",
    },
    "UINTAH": {
        "lat": 40.4555,
        "lng": -109.5287,
        "label": "Uintah County - county-level complaint, no address provided",
    },
}

KEEP_TERMS = [
    "h2s",
    "odor",
    "smell",
    "fumes",
    "air quality",
    "dust",
    "pm10",
    "noise",
    "vibration",
    "truck traffic",
    "flare",
    "flaring",
    "water contamination",
    "contamination",
    "headache",
    "asthma",
    "can't breathe",
    "sickness",
]

JUNK_SOURCE_FILES = [
    "ordinance",
    "general-plan",
    "crmp",
    "s1969",
    "00004302",
    "00004321",
]


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def has_any(text, terms):
    lower = str(text or "").lower()
    return any(term in lower for term in terms)


def is_junk_policy_record(record):
    source_file = str(record.get("source_file") or "").lower()
    description = str(record.get("description") or "").lower()

    if any(term in source_file for term in JUNK_SOURCE_FILES):
        return True

    if "whereas" in description and "ordinance" in description:
        return True

    return False


def get_coordinates(record):
    if record.get("suggested_lat") and record.get("suggested_lng"):
        return (
            float(record["suggested_lat"]),
            float(record["suggested_lng"]),
            record.get("suggested_location_label")
            or record.get("location_label")
            or "",
            record.get("location_confidence") or "manual_review_approximate",
        )

    county = str(record.get("county") or "").upper()
    fallback = COUNTY_FALLBACK.get(county)

    if fallback:
        return (
            fallback["lat"],
            fallback["lng"],
            fallback["label"],
            "county_level_no_address_provided",
        )

    return None, None, "", "needs_location_review"


shutil.copyfile(COMPLAINTS_FILE, BACKUP_FILE)

review_records = load_json(REVIEW_FILE)
complaints = load_json(COMPLAINTS_FILE)

existing_keys = {
    (
        str(c.get("source_file", "")),
        str(c.get("date", "")),
        str(c.get("description", ""))[:160],
    )
    for c in complaints
}

to_add = []
skipped = 0

for record in review_records:
    description = record.get("description", "")
    date = str(record.get("date") or record.get("year") or "")

    if not description or not date or date.lower() == "unknown":
        skipped += 1
        continue

    if is_junk_policy_record(record):
        skipped += 1
        continue

    if not has_any(description, KEEP_TERMS):
        skipped += 1
        continue

    key = (
        str(record.get("source_file", "")),
        date,
        str(description)[:160],
    )

    if key in existing_keys:
        skipped += 1
        continue

    lat, lng, location_label, location_confidence = get_coordinates(record)

    if not lat or not lng:
        skipped += 1
        continue

    new_record = {
        "id": f"verified_complaint_{len(complaints) + len(to_add) + 1:04d}",
        "type": record.get("type") or "Environmental Complaint",
        "complaint_type": record.get("type") or "Environmental Complaint",
        "description": description,
        "date": date,
        "year": str(record.get("year") or date[:4]),
        "county": record.get("county") or "Unknown",
        "lat": lat,
        "lng": lng,
        "source": record.get("source") or "Parsed public record",
        "source_file": record.get("source_file"),
        "speaker": "Public record / no address provided",
        "category": record.get("type") or "Environmental Complaint",
        "industry": record.get("industry") or "",
        "location_label": location_label,
        "location_confidence": location_confidence,
        "verification": "Documented public record - county-level marker if no address provided",
        "verified": True,
        "map_ready": True,
        "review_status": "map_ready_county_or_manual_location",
        "review_notes": record.get("review_notes") or "",
    }

    to_add.append(new_record)

complaints.extend(to_add)
save_json(COMPLAINTS_FILE, complaints)

print()
print("======================================")
print("COMPLAINTS PROMOTED WITH COUNTY FALLBACK")
print("======================================")
print(f"Review records read: {len(review_records)}")
print(f"Added: {len(to_add)}")
print(f"Skipped: {skipped}")
print(f"Total complaints now: {len(complaints)}")
print(f"Backup: {BACKUP_FILE}")
