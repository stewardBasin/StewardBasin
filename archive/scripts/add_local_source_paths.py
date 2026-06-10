import json
import shutil
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data"

FILES_TO_UPDATE = [
    DATA / "complaints.json",
    DATA / "deq_environmental_incidents_basin.json",
]

SEARCH_DIRS = [
    BASE / "extracted_text",
    DATA,
]

def build_file_index():
    index = {}
    for folder in SEARCH_DIRS:
        if not folder.exists():
            continue
        for path in folder.rglob("*"):
            if path.is_file():
                index.setdefault(path.name, str(path).replace("\\", "/"))
    return index

file_index = build_file_index()

for json_file in FILES_TO_UPDATE:
    backup = json_file.with_name(
        f"{json_file.stem}_before_local_sources_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    shutil.copyfile(json_file, backup)

    records = json.load(open(json_file, encoding="utf-8"))
    updated = 0

    for rec in records:
        source_file = rec.get("source_file")
        if source_file and source_file in file_index:
            rec["local_source_path"] = file_index[source_file]
            rec["source_url_status"] = rec.get("source_url_status") or "local_archive_only"
            updated += 1

    json.dump(records, open(json_file, "w", encoding="utf-8"), indent=2)

    print(json_file)
    print("Backup:", backup)
    print("Updated local paths:", updated)