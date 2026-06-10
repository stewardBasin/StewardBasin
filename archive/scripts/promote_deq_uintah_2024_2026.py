import os
import json
import shutil
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

NEW_FILE = os.path.join(BASE_DIR, "data", "deq_uintah_2024_2026_structured.json")
BASIN_FILE = os.path.join(BASE_DIR, "data", "deq_environmental_incidents_basin.json")

BACKUP_FILE = os.path.join(
    BASE_DIR,
    "data",
    f"deq_environmental_incidents_basin_before_uintah_2024_2026_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
)

shutil.copyfile(BASIN_FILE, BACKUP_FILE)

with open(NEW_FILE, "r", encoding="utf-8") as f:
    new_records = json.load(f)

with open(BASIN_FILE, "r", encoding="utf-8") as f:
    basin_records = json.load(f)

existing_ids = {
    str(r.get("derrid") or r.get("id") or "")
    for r in basin_records
}

to_add = []

for record in new_records:
    rid = str(record.get("derrid") or record.get("id") or "")

    if rid and rid in existing_ids:
        print(f"Skipping duplicate: {rid}")
        continue

    record["county"] = "UINTAH"
    record["map_ready"] = bool(
        record.get("the_geom") and record["the_geom"].get("coordinates")
    )

    to_add.append(record)

combined = basin_records + to_add

with open(BASIN_FILE, "w", encoding="utf-8") as f:
    json.dump(combined, f, indent=2)

print("Backup:", BACKUP_FILE)
print("Existing basin records:", len(basin_records))
print("New Uintah 2024-2026 records:", len(new_records))
print("Added:", len(to_add))
print("Total basin records now:", len(combined))