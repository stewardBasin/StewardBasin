import json, os, shutil
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASIN = os.path.join(BASE, "data", "deq_environmental_incidents_basin.json")
MAPPED = os.path.join(BASE, "data", "deq_duchesne_2020_2024.json")

backup = BASIN.replace(
    ".json", f"_backup_before_mapped_replace_{datetime.now():%Y%m%d_%H%M%S}.json"
)
shutil.copyfile(BASIN, backup)

basin = json.load(open(BASIN, encoding="utf-8"))
mapped = json.load(open(MAPPED, encoding="utf-8"))

mapped_by_id = {str(r.get("id") or r.get("derrid")): r for r in mapped}

replaced = 0
new_basin = []

for r in basin:
    rid = str(r.get("id") or r.get("derrid"))
    if rid in mapped_by_id:
        new_basin.append(mapped_by_id[rid])
        replaced += 1
    else:
        new_basin.append(r)

json.dump(new_basin, open(BASIN, "w", encoding="utf-8"), indent=2)

print("Backup:", backup)
print("Original basin:", len(basin))
print("New basin:", len(new_basin))
print("Replaced:", replaced)
print(
    "Coords in basin:",
    sum(1 for x in new_basin if x.get("the_geom") and x["the_geom"].get("coordinates")),
)
