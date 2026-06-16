import csv
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[3]

INFILE = ROOT / "archive/data/complaint_candidates_v2.csv"
OUTDIR = ROOT / "archive/data/deep_mining_review"
OUTDIR.mkdir(parents=True, exist_ok=True)

CONFIRMED_OUT = OUTDIR / "confirmed_complaint_candidates.csv"
TESTIMONY_OUT = OUTDIR / "public_testimony_candidates.csv"
RELEASE_OUT = OUTDIR / "environmental_release_candidates.csv"
FACILITY_OUT = OUTDIR / "facility_context_candidates.csv"
DISCARD_OUT = OUTDIR / "likely_duplicate_or_low_value.csv"

CONFIRMED_TERMS = [
    "odor complaint",
    "dust complaint",
    "noise complaint",
    "truck traffic complaint",
    "chemical smell",
    "hydrogen sulfide odor",
    "h2s odor",
    "wastewater odor",
    "noxious fumes",
    "citizen complained",
    "resident complained",
    "complaint was filed",
    "complaints were received",
]

TESTIMONY_TERMS = [
    "raised concerns",
    "public concern",
    "public testimony",
    "residents expressed concern",
    "citizens expressed concern",
    "neighbors objected",
    "public opposition",
]

RELEASE_TERMS = [
    "produced water",
    "release",
    "spill",
    "leak",
    "discharge",
    "containment pond",
    "crude oil",
    "diesel",
    "hydraulic oil",
]

FACILITY_TERMS = [
    "conditional use permit",
    "cup",
    "rewater",
    "wells draw",
    "nine mile",
    "blue diamond",
    "proppants",
    "gravel pit",
    "crusher",
    "landfill",
    "evaporation pond",
    "wastewater facility",
]

DUPLICATE_PATH_HINTS = [
    "archive/sources/deq_2006_2015_records",
    "archive/sources/deq_2016_2019_records",
    "archive/sources/deq_missing_local_records",
    "archive/sources/complaint_records",
    "archive/clean/",
    "archive/data/",
]


def blob(row):
    return " ".join(
        str(row.get(k, ""))
        for k in ["source_file", "matched_phrase", "locations", "snippet"]
    ).lower()


def has_any(text, terms):
    return any(t.lower() in text for t in terms)


def classify(row):
    text = blob(row)
    source_file = row.get("source_file", "").replace("\\", "/")

    # First: remove things that are clearly already derived/archive copies.
    if any(hint in source_file for hint in DUPLICATE_PATH_HINTS):
        return "discard"

    # Strongest: actual complaint language.
    if has_any(text, CONFIRMED_TERMS):
        return "confirmed"

    # Public testimony/concerns are useful but not the same as formal complaints.
    if has_any(text, TESTIMONY_TERMS):
        return "testimony"

    # DEQ/incident style records are environmental releases, not complaints.
    if has_any(text, RELEASE_TERMS):
        return "release"

    # Facility/project context.
    if has_any(text, FACILITY_TERMS):
        return "facility"

    return "discard"


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


with open(INFILE, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

for r in rows:
    r["classification"] = classify(r)

groups = {
    "confirmed": [],
    "testimony": [],
    "release": [],
    "facility": [],
    "discard": [],
}

for r in rows:
    groups[r["classification"]].append(r)

fieldnames = list(rows[0].keys()) if rows else []

write_csv(CONFIRMED_OUT, groups["confirmed"], fieldnames)
write_csv(TESTIMONY_OUT, groups["testimony"], fieldnames)
write_csv(RELEASE_OUT, groups["release"], fieldnames)
write_csv(FACILITY_OUT, groups["facility"], fieldnames)
write_csv(DISCARD_OUT, groups["discard"], fieldnames)

print("\nCLASSIFICATION COMPLETE")
print("=======================")
for k, v in groups.items():
    print(f"{k}: {len(v)}")

print("\nOutputs:")
print(CONFIRMED_OUT)
print(TESTIMONY_OUT)
print(RELEASE_OUT)
print(FACILITY_OUT)
print(DISCARD_OUT)

print("\nMatched phrases in confirmed:")
print(Counter(r.get("matched_phrase") for r in groups["confirmed"]))
