import json
import shutil
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

SOURCE_FILE = BASE_DIR / "data" / "verified_complaint_candidates.json"
COMPLAINTS_FILE = BASE_DIR / "data" / "complaints.json"

BACKUP_FILE = (
    BASE_DIR
    / "data"
    / f"complaints_before_verified_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
)

shutil.copyfile(COMPLAINTS_FILE, BACKUP_FILE)

with open(SOURCE_FILE, "r", encoding="utf-8") as f:
    candidates = json.load(f)

with open(COMPLAINTS_FILE, "r", encoding="utf-8") as f:
    complaints = json.load(f)

existing_keys = {
    (
        str(c.get("source_file", "")),
        str(c.get("description", ""))[:120],
        str(c.get("date", "")),
    )
    for c in complaints
}

to_add = []

for item in candidates:
    # Only promote stronger records. Leave locationless ones for review,
    # but still allow them into chart if they have a date.
    description = item.get("description", "")
    date = item.get("date") or item.get("year") or ""

    if not description or not date:
        continue

    key = (
        str(item.get("source_file", "")),
        str(description)[:120],
        str(date),
    )

    if key in existing_keys:
        continue

    to_add.append(
        {
            "id": f"verified_candidate_{len(complaints) + len(to_add) + 1:04d}",
            "type": item.get("type")
            or item.get("category")
            or "Environmental Complaint",
            "complaint_type": item.get("category")
            or item.get("type")
            or "Environmental Complaint",
            "description": description,
            "date": str(date),
            "year": str(item.get("year") or str(date)[:4]),
            "county": item.get("county") or "Unknown",
            "lat": item.get("lat") or "",
            "lng": item.get("lng") or "",
            "source": item.get("source") or "Parsed public record",
            "source_file": item.get("source_file"),
            "speaker": item.get("speaker") or "Public record / needs review",
            "category": item.get("category")
            or item.get("type")
            or "Environmental Complaint",
            "industry": item.get("industry") or "",
            "location_label": item.get("location_label") or "",
            "location_confidence": item.get("location_confidence")
            or "needs_location_review",
            "map_ready": bool(item.get("lat") and item.get("lng")),
            "verification": "Candidate - needs human review",
            "review_status": "promoted_to_complaints_for_chart_review",
        }
    )

complaints.extend(to_add)

with open(COMPLAINTS_FILE, "w", encoding="utf-8") as f:
    json.dump(complaints, f, indent=2)

print("Backup:", BACKUP_FILE)
print("Existing complaints:", len(complaints) - len(to_add))
print("Candidates read:", len(candidates))
print("Added:", len(to_add))
print("Total complaints:", len(complaints))
