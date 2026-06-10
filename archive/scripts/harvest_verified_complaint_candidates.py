import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"

INPUT_FILES = [
    DATA_DIR / "complaint_h2s_findings.json",
    DATA_DIR / "h2s_odor_complaints.json",
    DATA_DIR / "dust_complaints.json",
    DATA_DIR / "noise_flaring_complaints.json",
]

OUTPUT_FILE = DATA_DIR / "verified_complaint_candidates.json"

STRONG_PUBLIC_COMMENT_TERMS = [
    "raised concerns",
    "public comments",
    "public comment",
    "resident",
    "residents",
    "citizen",
    "testified",
    "asked about",
    "complaint",
    "complained",
    "opposed",
    "concern",
    "concerns",
]

ENVIRONMENTAL_TERMS = [
    "odor",
    "h2s",
    "hydrogen sulfide",
    "air quality",
    "dust",
    "pm10",
    "noise",
    "vibration",
    "flare",
    "flaring",
    "truck traffic",
    "mosquitoes",
    "evaporation",
    "wildlife",
    "water",
    "contamination",
]

JUNK_TERMS = [
    "senate",
    "house",
    "committee recommends",
    "criminal",
    "court",
    "jail",
    "prison",
    "motorcycle profiling",
    "school",
    "student",
    "teacher",
    "ordinance shall",
    "operators shall",
]


def load_json(path):
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        data = json.load(f)
    return data if isinstance(data, list) else [data]


def clean_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def get_blob(record):
    parts = [
        record.get("description", ""),
        record.get("category", ""),
        record.get("type", ""),
        record.get("source_file", ""),
    ]

    for match in record.get("matches", []):
        parts.append(match.get("snippet", ""))
        parts.append(match.get("keyword", ""))

    return clean_text(" ".join(parts))


def has_any(blob, terms):
    lower = blob.lower()
    return [term for term in terms if term in lower]


def guess_category(matches):
    m = set(matches)

    if "h2s" in m or "hydrogen sulfide" in m or "odor" in m:
        return "H2S / Odor"
    if "dust" in m or "pm10" in m:
        return "Dust / PM10"
    if "noise" in m or "vibration" in m or "flare" in m or "flaring" in m:
        return "Noise / Flaring"
    if "air quality" in m:
        return "Air Quality"
    if "truck traffic" in m:
        return "Truck Traffic"
    if "water" in m or "contamination" in m:
        return "Water / Contamination"

    return "Environmental Complaint"


candidates = []
seen = set()

for input_file in INPUT_FILES:
    for record in load_json(input_file):
        blob = get_blob(record)

        public_terms = has_any(blob, STRONG_PUBLIC_COMMENT_TERMS)
        env_terms = has_any(blob, ENVIRONMENTAL_TERMS)
        junk_terms = has_any(blob, JUNK_TERMS)

        if junk_terms:
            continue

        if not public_terms or not env_terms:
            continue

        key = (
            record.get("source_file"),
            record.get("year"),
            blob[:200],
        )

        if key in seen:
            continue

        seen.add(key)

        candidates.append(
            {
                "type": guess_category(env_terms),
                "description": blob[:1200],
                "date": record.get("date") or record.get("year") or "",
                "year": record.get("year") or "",
                "county": record.get("county") or "Unknown",
                "source": "Parsed public record",
                "source_file": record.get("source_file"),
                "category": guess_category(env_terms),
                "matched_public_comment_terms": public_terms,
                "matched_environmental_terms": env_terms,
                "lat": record.get("lat") or "",
                "lng": record.get("lng") or "",
                "location_label": record.get("location_label") or "",
                "location_confidence": record.get("location_confidence")
                or "needs_location_review",
                "map_ready": bool(record.get("lat") and record.get("lng")),
                "review_status": "verified_candidate_needs_human_review",
                "source_input_file": str(input_file.relative_to(BASE_DIR)),
            }
        )

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(candidates, f, indent=2)

print("Verified complaint candidates:", len(candidates))
print("Saved:", OUTPUT_FILE)
