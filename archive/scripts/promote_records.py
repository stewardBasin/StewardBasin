import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CLEAN_DIR = os.path.join(BASE_DIR, "clean")

INPUT_FILE = os.path.join(CLEAN_DIR, "needs_review_industrial.json")

KEEP_FILE = os.path.join(CLEAN_DIR, "promoted_keep.json")
MAYBE_FILE = os.path.join(CLEAN_DIR, "promoted_maybe.json")
JUNK_FILE = os.path.join(CLEAN_DIR, "promoted_junk.json")

KEEP_TERMS = [
    "ozone",
    "air quality",
    "pm2.5",
    "pm10",
    "particulate",
    "dust",
    "fugitive dust",
    "odor",
    "h2s",
    "hydrogen sulfide",
    "rotten egg",
    "spill",
    "release",
    "produced water",
    "wastewater",
    "groundwater",
    "contamination",
    "oil",
    "gas",
    "well",
    "drilling",
    "flare",
    "flaring",
    "compressor",
    "notice of violation",
    "noncompliance",
    "air conservation act",
    "clean air act",
    "emissions",
    "conditional use permit",
    "planning commission",
    "industrial",
    "mine",
    "sand",
    "gravel",
    "data center",
    "power plant"
]

JUNK_TERMS = [
    "student data",
    "school",
    "teacher",
    "hospital emergency room",
    "emergency room task force",
    "driver license",
    "motor vehicle",
    "alcohol",
    "child support",
    "retirement",
    "election",
    "wildfire and public nuisance",
    "catastrophic wildfire",
    "horse racing",
    "tobacco",
    "smoking",
    "uninsured motorist",
    "birthing facility",
    "mortgage",
    "court",
    "criminal",
    "juvenile",
    "parole"
]


def load_json(path):
    if not os.path.exists(path):
        print(f"Missing input file: {path}")
        return []

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def get_blob(record):
    parts = [
        str(record.get("id", "")),
        str(record.get("category", "")),
        str(record.get("source_file", "")),
        str(record.get("county", "")),
    ]

    for match in record.get("matches", []):
        parts.append(str(match.get("keyword", "")))
        parts.append(str(match.get("snippet", "")))

    return " ".join(parts).lower()


def score_record(record):
    blob = get_blob(record)

    keep_score = sum(1 for term in KEEP_TERMS if term in blob)
    junk_score = sum(1 for term in JUNK_TERMS if term in blob)

    return keep_score, junk_score


records = load_json(INPUT_FILE)

keep = []
maybe = []
junk = []

for record in records:
    keep_score, junk_score = score_record(record)

    record["promote_keep_score"] = keep_score
    record["promote_junk_score"] = junk_score

    if junk_score >= 2 and keep_score < 3:
        record["promote_status"] = "junk"
        junk.append(record)

    elif keep_score >= 3 and junk_score == 0:
        record["promote_status"] = "keep_needs_review"
        keep.append(record)

    else:
        record["promote_status"] = "maybe_manual_review"
        maybe.append(record)

save_json(KEEP_FILE, keep)
save_json(MAYBE_FILE, maybe)
save_json(JUNK_FILE, junk)

print("\n====================")
print("PROMOTION TRIAGE COMPLETE")
print("====================")
print(f"Keep / needs review: {len(keep)}")
print(f"Maybe / manual review: {len(maybe)}")
print(f"Junk: {len(junk)}")
print(f"Saved: {KEEP_FILE}")
print(f"Saved: {MAYBE_FILE}")
print(f"Saved: {JUNK_FILE}")