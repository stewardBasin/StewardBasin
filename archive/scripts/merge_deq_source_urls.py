import json
import shutil
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data"

MAIN = DATA / "deq_environmental_incidents_basin.json"

SOURCE_FILES = [
    DATA / "deq_incidents_classified.json",
    DATA / "deq_incidents_pre2016.json",
    DATA / "deq_incidents_2016_present.json",
]

backup = MAIN.with_name(
    f"deq_environmental_incidents_basin_before_source_url_merge_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
)
shutil.copyfile(MAIN, backup)


def keys_for(record):
    keys = set()
    for field in ["derrid", "id"]:
        if record.get(field):
            keys.add(str(record[field]))
    raw = record.get("raw_record") or {}
    for field in ["id", "objectid"]:
        if raw.get(field):
            keys.add(str(raw[field]))
    return keys


source_lookup = {}

for path in SOURCE_FILES:
    if not path.exists():
        print("Missing:", path)
        continue

    records = json.load(open(path, encoding="utf-8"))
    for record in records:
        url = record.get("source_url")
        if not url:
            continue

        for key in keys_for(record):
            source_lookup[key] = url

main = json.load(open(MAIN, encoding="utf-8"))

updated = 0

for record in main:
    if record.get("source_url"):
        continue

    for key in keys_for(record):
        if key in source_lookup:
            record["source_url"] = source_lookup[key]
            updated += 1
            break

json.dump(main, open(MAIN, "w", encoding="utf-8"), indent=2)

print("Backup:", backup)
print("Source lookup keys:", len(source_lookup))
print("Updated records:", updated)
