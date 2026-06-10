import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

NEW_FILE = os.path.join(BASE_DIR, "data", "deq_uintah_2020_2024.json")
BASIN_FILE = os.path.join(BASE_DIR, "data", "deq_environmental_incidents_basin.json")

with open(NEW_FILE, "r", encoding="utf-8") as f:
    new_records = json.load(f)

with open(BASIN_FILE, "r", encoding="utf-8") as f:
    basin_records = json.load(f)

existing_ids = {str(r.get("derrid") or r.get("id") or "") for r in basin_records}

to_add = []
for record in new_records:
    rid = str(record.get("derrid") or record.get("id") or "")
    if rid and rid in existing_ids:
        continue
    to_add.append(record)

combined = basin_records + to_add

with open(BASIN_FILE, "w", encoding="utf-8") as f:
    json.dump(combined, f, indent=2)

print("Existing basin records:", len(basin_records))
print("New 2020-2024 records:", len(new_records))
print("Added:", len(to_add))
print("Total basin records now:", len(combined))
