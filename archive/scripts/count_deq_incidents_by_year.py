import json
import os
import re
from collections import Counter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

INPUT_FILE = os.path.join(DATA_DIR, "deq_incidents_classified.json")

def get_year(value):
    if not value:
        return None
    match = re.search(r"(19|20)\d{2}", str(value))
    return match.group() if match else None

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    records = json.load(f)

counts = Counter()

for record in records:
    year = get_year(record.get("date"))
    if year:
        counts[year] += 1

print("\nDEQ incidents by year:")
for year in sorted(counts):
    print(f"{year}: {counts[year]}")

print("\nLatest year in file:", max(counts) if counts else "No dates found")
print("Total dated records:", sum(counts.values()))
print("Total records:", len(records))