import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASIN_FILE = os.path.join(BASE_DIR, "data", "deq_environmental_incidents_basin.json")

with open(BASIN_FILE, "r", encoding="utf-8") as f:
    records = json.load(f)

seen = set()
deduped = []
removed = 0

for record in records:
    rid = str(record.get("derrid") or record.get("id") or "").strip()

    if not rid:
        deduped.append(record)
        continue

    if rid in seen:
        removed += 1
        continue

    seen.add(rid)
    deduped.append(record)

with open(BASIN_FILE, "w", encoding="utf-8") as f:
    json.dump(deduped, f, indent=2)

print("Before:", len(records))
print("After:", len(deduped))
print("Removed duplicates:", removed)