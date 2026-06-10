import json
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JSON_PATH = ROOT / "archive" / "data" / "complaints.json"

LINK_FILES = [
    ROOT / "archive" / "county_links.txt",
    ROOT / "archive" / "complaint_h2s_links.txt",
    ROOT / "archive" / "uintah_public_record_links.txt",
    ROOT / "archive" / "scripts" / "county_links_master.txt",
    ROOT / "archive" / "scripts" / "complaint_h2s_links_master.txt",
]

BACKUP = JSON_PATH.with_name(
    f"complaints_before_filename_source_url_match_{datetime.now():%Y%m%d_%H%M%S}.json"
)
shutil.copyfile(JSON_PATH, BACKUP)

records = json.load(open(JSON_PATH, encoding="utf-8"))

links = []
for link_file in LINK_FILES:
    if not link_file.exists():
        continue
    for line in link_file.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if line.startswith("SCANNED:"):
            line = line.replace("SCANNED:", "").strip()
        if line.startswith("http"):
            links.append(line)

updated = 0
missing_source_file = 0
no_match = 0

for r in records:
    source_file = r.get("source_file")

    if not source_file:
        missing_source_file += 1
        continue

    if r.get("source_url"):
        continue

    base = Path(source_file).stem

    match = next((url for url in links if base.lower() in url.lower()), None)

    if match:
        r["source_url"] = match
        r["source_url_status"] = "matched_from_source_filename"
        updated += 1
    else:
        no_match += 1

json.dump(records, open(JSON_PATH, "w", encoding="utf-8"), indent=2)

print("Backup:", BACKUP)
print("Links loaded:", len(links))
print("Source URLs added:", updated)
print("Missing source_file:", missing_source_file)
print("No match:", no_match)
