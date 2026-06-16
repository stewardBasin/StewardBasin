import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

INPUT = ROOT / "archive/data/deep_mining_review/confirmed_complaint_candidates.csv"
OUTPUT = ROOT / "archive/data/deep_mining_review/promote_ready_complaints.csv"

KEEP_TERMS = [
    "resident complained",
    "citizen complained",
    "public complained",
    "noise complaint",
    "dust complaint",
    "odor complaint",
    "noxious fumes",
    "chemical smell",
    "public testimony",
    "raised concerns",
    "hydrogen sulfide odor",
    "h2s odor",
    "flare noise",
]

rows = []

with open(INPUT, encoding="utf-8") as f:

    reader = csv.DictReader(f)

    for r in reader:

        blob = r.get("snippet", "").lower() + " " + r.get("matched_phrase", "").lower()

        if any(term in blob for term in KEEP_TERMS):
            rows.append(r)

with open(OUTPUT, "w", newline="", encoding="utf-8") as f:

    writer = csv.DictWriter(f, fieldnames=reader.fieldnames)

    writer.writeheader()
    writer.writerows(rows)

print("Promote-ready records:", len(rows))
print("Saved:", OUTPUT)
