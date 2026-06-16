import csv
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[3]

INFILE = ROOT / "archive/data/deep_mining_review/targeted_entity_clean/targeted_entity_hits_clean.csv"
OUTDIR = ROOT / "archive/data/deep_mining_review/governance_classified"
OUTDIR.mkdir(parents=True, exist_ok=True)

OUTPUTS = {
    "complaint_candidate": OUTDIR / "complaint_candidates.csv",
    "public_testimony": OUTDIR / "public_testimony.csv",
    "industrial_project": OUTDIR / "industrial_projects.csv",
    "governance_record": OUTDIR / "governance_records.csv",
    "water_infrastructure": OUTDIR / "water_infrastructure.csv",
    "low_priority": OUTDIR / "low_priority.csv",
}

COMPLAINT_TERMS = [
    "odor complaint", "dust complaint", "noise complaint",
    "noxious fumes", "chemical smell", "h2s", "hydrogen sulfide",
    "wastewater odor", "pond odor", "complained", "complaints received",
]

TESTIMONY_TERMS = [
    "raised concerns", "public concern", "public testimony",
    "opponents", "objected", "concern", "little guy",
    "front door", "nearby property owners",
]

INDUSTRIAL_TERMS = [
    "blue diamond", "4-c farms", "4c farms", "proppants",
    "integrated water management", "wasatch energy",
    "sand excavation", "sand processing", "surface mine",
    "crusher", "rock crushing", "labor camp", "conditional use permit", "cup",
]

GOVERNANCE_TERMS = [
    "planning commission", "county commission", "public hearing",
    "rezone", "ordinance", "resolution", "approved", "motion passed",
    "recommendation", "zoning",
]

WATER_TERMS = [
    "hancock cove", "sewer", "culinary water", "water district",
    "board of trustees", "annexation", "wastewater authority",
]


def text(row):
    return " ".join(str(row.get(k, "")) for k in row.keys()).lower()


def has_any(blob, terms):
    return any(term in blob for term in terms)


def classify(row):
    blob = text(row)

    if has_any(blob, COMPLAINT_TERMS):
        return "complaint_candidate"

    if has_any(blob, TESTIMONY_TERMS):
        return "public_testimony"

    if has_any(blob, WATER_TERMS):
        return "water_infrastructure"

    if has_any(blob, INDUSTRIAL_TERMS):
        return "industrial_project"

    if has_any(blob, GOVERNANCE_TERMS):
        return "governance_record"

    return "low_priority"


with open(INFILE, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

for row in rows:
    row["classification"] = classify(row)

groups = {k: [] for k in OUTPUTS}

for row in rows:
    groups[row["classification"]].append(row)

fieldnames = list(rows[0].keys()) if rows else []

for name, path in OUTPUTS.items():
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(groups[name])

print("\nGOVERNANCE CANDIDATE CLASSIFICATION COMPLETE")
print("===========================================")

for name, records in groups.items():
    print(f"{name}: {len(records)}")

print("\nMatched terms:")
print(Counter(row.get("matched_term") for row in rows))

print("\nOutput folder:")
print(OUTDIR)