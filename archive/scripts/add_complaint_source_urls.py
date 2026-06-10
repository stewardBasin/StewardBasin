import json
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JSON_PATH = ROOT / "archive" / "data" / "complaints.json"

BACKUP = JSON_PATH.with_name(
    f"complaints_before_source_urls_{datetime.now():%Y%m%d_%H%M%S}.json"
)
shutil.copyfile(JSON_PATH, BACKUP)

records = json.load(open(JSON_PATH, encoding="utf-8"))

source_map = {
    "Duchesne-County-Planning-Commission-4_02_2026.txt": "https://duchesne.utah.gov/wp-content/uploads/2026/05/Duchesne-County-Planning-Commission-4_02_2026.pdf",
    "December-7-2016.txt": "https://www.duchesne.utah.gov/wp-content/uploads/2017/04/December-7-2016.pdf",
    "General-Plan-2024-1.txt": "https://duchesne.utah.gov/wp-content/uploads/2024/12/General-Plan-2024-1.pdf",
}

updated = 0

for r in records:
    source_file = r.get("source_file")
    if source_file in source_map:
        r["source_url"] = source_map[source_file]
        r["source_url_status"] = "matched_original_pdf"
        updated += 1

json.dump(records, open(JSON_PATH, "w", encoding="utf-8"), indent=2)

print("Backup:", BACKUP)
print("Updated source URLs:", updated)
