import json
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

JSON_PATH = ROOT / "archive" / "data" / "complaints.json"

BACKUP = JSON_PATH.with_name(
    f"complaints_before_duplicate_review_{datetime.now():%Y%m%d_%H%M%S}.json"
)

shutil.copyfile(JSON_PATH, BACKUP)

records = json.load(open(JSON_PATH, encoding="utf-8"))

# Keep record 26
records[26]["type"] = "Public Testimony"
records[26]["category"] = "Public Testimony"
records[26]["record_kind"] = "public_testimony"

records[26]["review_note"] = (
    "Originally parsed as H2S/Odor complaint. "
    "Manual review determined this is public testimony "
    "from Duchesne County Planning Commission minutes."
)

# Flag record 43 instead of deleting it
records[43]["review_status"] = "duplicate_record"
records[43]["exclude_from_map"] = True
records[43]["exclude_from_charts"] = True

json.dump(records, open(JSON_PATH, "w", encoding="utf-8"), indent=2)

print("Backup:", BACKUP)
print("Updated record 26 -> Public Testimony")
print("Flagged record 43 as duplicate")
