import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

NEW_FILE = os.path.join(BASE_DIR, "data", "deq_duchesne_2024_2026_structured.json")
BASIN_FILE = os.path.join(BASE_DIR, "data", "deq_environmental_incidents_basin.json")
BACKUP_FILE = os.path.join(
    BASE_DIR, "data", "deq_environmental_incidents_basin_before_2024_2026_import.json"
)

with open(NEW_FILE, "r", encoding="utf-8") as f:
    new_records = json.load(f)

with open(BASIN_FILE, "r", encoding="utf-8") as f:
    basin_records = json.load(f)

# One-time safety backup
if not os.path.exists(BACKUP_FILE):
    with open(BACKUP_FILE, "w", encoding="utf-8") as f:
        json.dump(basin_records, f, indent=2)

existing_ids = {
    str(record.get("derrid") or record.get("id") or "") for record in basin_records
}

records_to_add = []

for record in new_records:
    record_id = str(record.get("derrid") or record.get("id") or "")

    if record_id and record_id in existing_ids:
        print(f"Skipping duplicate: {record_id}")
        continue

    records_to_add.append(record)

combined = basin_records + records_to_add

with open(BASIN_FILE, "w", encoding="utf-8") as f:
    json.dump(combined, f, indent=2)

print()
print("======================================")
print("DEQ DUCHESNE 2024-2026 PROMOTED")
print("======================================")
print(f"Existing basin records: {len(basin_records)}")
print(f"New structured records: {len(new_records)}")
print(f"Added: {len(records_to_add)}")
print(f"Total basin records now: {len(combined)}")
print(f"Updated: {BASIN_FILE}")
print(f"Backup: {BACKUP_FILE}")
