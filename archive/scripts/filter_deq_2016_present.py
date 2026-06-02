import json
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

INPUT_FILE = os.path.join(DATA_DIR, "deq_incidents_classified.json")
OUTPUT_FILE = os.path.join(DATA_DIR, "deq_incidents_2016_present.json")


def extract_year(date_value):
    if not date_value:
        return None

    match = re.search(r"(19|20)\d{2}", str(date_value))

    if match:
        return int(match.group())

    return None


with open(INPUT_FILE, "r", encoding="utf-8") as f:
    incidents = json.load(f)

filtered = []

for incident in incidents:
    year = extract_year(incident.get("date"))

    if year and year >= 2016:
        filtered.append(incident)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(filtered, f, indent=2)

print("\n==============================")
print("DEQ INCIDENT FILTER")
print("==============================")
print(f"Original records: {len(incidents)}")
print(f"2016-present:     {len(filtered)}")
print(f"Saved: {OUTPUT_FILE}")