import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(BASE_DIR, "data")
CLEAN_DIR = os.path.join(BASE_DIR, "clean")

os.makedirs(CLEAN_DIR, exist_ok=True)

COMPLAINT_FINDINGS = os.path.join(DATA_DIR, "complaint_h2s_findings.json")
ENTITY_FINDINGS = os.path.join(DATA_DIR, "entity_findings.json")

INDUSTRIAL_OUTPUT = os.path.join(CLEAN_DIR, "needs_review_industrial.json")
JUNK_OUTPUT = os.path.join(CLEAN_DIR, "likely_junk.json")
ENTITY_OUTPUT = os.path.join(CLEAN_DIR, "clean_entity_mentions.json")

GOOD_TERMS = [
    "oil", "gas", "well", "drilling", "frack", "frac",
    "sand", "mine", "industrial", "facility", "plant",
    "emissions", "odor", "h2s", "hydrogen sulfide",
    "ozone", "pm2.5", "pm10", "dust", "fugitive dust",
    "spill", "release", "wastewater", "produced water",
    "contamination", "groundwater", "violation",
    "noncompliance", "notice of violation", "complaint",
    "wetlands", "truck traffic", "road impacts",
    "conditional use permit", "cup", "processing facility"
]

JUNK_TERMS = [
    "abandoned horse",
    "open range",
    "school",
    "student",
    "teacher",
    "sample ballot",
    "election",
    "pledge of allegiance",
    "house journal",
    "senate journal",
    "public education base budget"
]

ENTITY_KEEP_TERMS = [
    "conditional use permit",
    "cup",
    "planning commission",
    "industrial",
    "oil",
    "gas",
    "mine",
    "sand",
    "facility",
    "processing",
    "water",
    "wastewater",
    "emissions",
    "odor",
    "road",
    "truck",
    "violation",
    "complaint",
    "hearing"
]


def load_json(path):
    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def text_blob(record):
    parts = []

    for key in ["snippet", "category", "keyword", "title", "description", "source_file"]:
        value = record.get(key)

        if value:
            parts.append(str(value))

    if "matches" in record:
        for match in record["matches"]:
            parts.append(match.get("snippet", ""))
            parts.append(match.get("keyword", ""))

    return " ".join(parts).lower()


def score_record(record):
    blob = text_blob(record)

    good_score = sum(1 for term in GOOD_TERMS if term in blob)
    junk_score = sum(1 for term in JUNK_TERMS if term in blob)

    return good_score, junk_score


def triage_complaints(records):
    useful = []
    junk = []

    for record in records:
        good_score, junk_score = score_record(record)

        reviewed = dict(record)
        reviewed["triage_good_score"] = good_score
        reviewed["triage_junk_score"] = junk_score

        if junk_score > 0 and good_score == 0:
            reviewed["triage_status"] = "likely_junk"
            junk.append(reviewed)
        elif good_score >= 2:
            reviewed["triage_status"] = "needs_human_review"
            useful.append(reviewed)
        else:
            reviewed["triage_status"] = "uncertain"
            junk.append(reviewed)

    return useful, junk


def triage_entities(records):
    clean_entities = []

    for record in records:
        blob = text_blob(record)

        if any(term in blob for term in ENTITY_KEEP_TERMS):
            cleaned = dict(record)
            cleaned["triage_status"] = "entity_relevant_needs_review"
            clean_entities.append(cleaned)

    return clean_entities


complaint_records = load_json(COMPLAINT_FINDINGS)
entity_records = load_json(ENTITY_FINDINGS)

useful_complaints, likely_junk = triage_complaints(complaint_records)
clean_entities = triage_entities(entity_records)

save_json(INDUSTRIAL_OUTPUT, useful_complaints)
save_json(JUNK_OUTPUT, likely_junk)
save_json(ENTITY_OUTPUT, clean_entities)

print("\n====================")
print("TRIAGE COMPLETE")
print("====================")
print(f"Useful complaint/environment records: {len(useful_complaints)}")
print(f"Likely junk records: {len(likely_junk)}")
print(f"Relevant entity records: {len(clean_entities)}")
print(f"Saved: {INDUSTRIAL_OUTPUT}")
print(f"Saved: {JUNK_OUTPUT}")
print(f"Saved: {ENTITY_OUTPUT}")