import csv
import json
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

INPUT = (
    ROOT
    / "archive/data/deep_mining_review/governance_classified/industrial_projects.csv"
)
OUTPUT = ROOT / "archive/data/industrial_projects.json"

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

if OUTPUT.exists():
    backup = OUTPUT.with_name(
        f"industrial_projects_before_promote_{datetime.now():%Y%m%d_%H%M%S}.json"
    )
    shutil.copyfile(OUTPUT, backup)
else:
    backup = None
    OUTPUT.write_text("[]", encoding="utf-8")


def clean(v):
    return " ".join(str(v or "").split())


def infer_entity(row):
    blob = clean(row.get("matched_term", "") + " " + row.get("snippet", "")).lower()

    if "blue diamond" in blob:
        return "Blue Diamond Proppants LLC"
    if "4-c farms" in blob or "4c farms" in blob:
        return "4-C Farms LLC"
    if "integrated water management" in blob:
        return "Integrated Water Management LLC"
    if "wasatch energy" in blob:
        return "Wasatch Energy Management LLC"
    if "vaibhav shree" in blob:
        return "Vaibhav Shree LLC"

    return clean(row.get("matched_term"))


def infer_project_type(row):
    blob = clean(row.get("snippet", "")).lower()

    if "surface mine" in blob or "surface mining" in blob:
        return "surface_mining"
    if "sand" in blob and ("excavation" in blob or "processing" in blob):
        return "industrial_sand_excavation_processing"
    if "rock crushing" in blob or "crusher" in blob:
        return "rock_crushing"
    if "labor camp" in blob:
        return "labor_camp"
    if "conditional use permit" in blob or "cup" in blob:
        return "conditional_use_permit"

    return "industrial_project"


def infer_tags(row):
    blob = clean(row.get("snippet", "")).lower()
    tags = []

    checks = {
        "surface mining": ["surface mine", "surface mining"],
        "sand/gravel": ["sand", "gravel"],
        "rock crushing": ["rock crushing", "crusher"],
        "truck traffic": ["truck", "haul", "transport"],
        "dust": ["dust"],
        "water": ["water", "wet plant", "sewer"],
        "wastewater": ["wastewater", "produced water"],
        "labor camp": ["labor camp"],
        "conditional use permit": ["conditional use permit", "cup"],
        "Blue Bench": ["blue bench"],
        "Arcadia": ["arcadia"],
        "Roosevelt": ["roosevelt"],
        "Fruitland": ["fruitland"],
    }

    for tag, words in checks.items():
        if any(w in blob for w in words):
            tags.append(tag)

    return sorted(set(tags))


def infer_date_from_source(source_file):
    name = Path(source_file).name

    # Handles things like 06-05-24.txt or 10-4-23.txt
    stem = name.replace(".txt", "").replace("_Combined", "")
    parts = stem.split("-")

    if len(parts) >= 3:
        try:
            month = int(parts[0])
            day = int(parts[1])
            year = int(parts[2])
            if year < 100:
                year += 2000
            return f"{year:04d}-{month:02d}-{day:02d}"
        except Exception:
            return None

    return None


existing = json.load(open(OUTPUT, encoding="utf-8"))

seen = set()
for r in existing:
    key = (
        r.get("source_file"),
        r.get("entity"),
        r.get("summary"),
    )
    seen.add(key)

rows = []
with open(INPUT, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

added = 0

for i, row in enumerate(rows, start=1):
    source_file = clean(row.get("source_file"))
    entity = infer_entity(row)
    summary = clean(row.get("snippet"))

    key = (source_file, entity, summary)
    if key in seen:
        continue

    record = {
        "id": f"industrial_project_{len(existing) + added + 1:04d}",
        "record_type": "industrial_project",
        "project_type": infer_project_type(row),
        "entity": entity,
        "matched_term": clean(row.get("matched_term")),
        "county": "Duchesne" if "Duchesne" in clean(row.get("locations")) else None,
        "locations": clean(row.get("locations")),
        "date": infer_date_from_source(source_file),
        "issue_tags": infer_tags(row),
        "summary": summary,
        "source_file": source_file,
        "source_kind": clean(row.get("source_kind")),
        "review_status": "needs_human_review",
        "retrieved_from_public_source": True,
        "archive_method": "automated_public_record_capture",
        "archive_verification_level": None,
        "dedupe_fingerprint": clean(row.get("dedupe_fingerprint")),
    }

    existing.append(record)
    seen.add(key)
    added += 1

json.dump(existing, open(OUTPUT, "w", encoding="utf-8"), indent=2)

print("Industrial project promotion complete")
print("Input rows:", len(rows))
print("Added:", added)
print("Total industrial project records:", len(existing))
print("Output:", OUTPUT)

if backup:
    print("Backup:", backup)
