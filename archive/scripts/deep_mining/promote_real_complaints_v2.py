from pathlib import Path
import csv
import re

ROOT = Path(__file__).resolve().parents[3]
ARCHIVE = ROOT / "archive"
OUT = ROOT / "archive/data/complaint_candidates_v2.csv"

HIGH_CONFIDENCE_PHRASES = [
    "received complaints",
    "complaints were received",
    "complaint was filed",
    "resident complained",
    "residents complained",
    "neighbor complained",
    "citizen complained",
    "public complained",
    "residents expressed concern",
    "citizens expressed concern",
    "public expressed concern",
    "raised concerns",
    "public concern",
    "resident concern",
    "citizen concern",
    "public testimony",
    "odor complaint",
    "dust complaint",
    "noise complaint",
    "truck traffic complaint",
    "air quality concern",
    "odor nuisance",
    "chemical smell",
    "noxious fumes",
    "hydrogen sulfide odor",
    "h2s odor",
    "flare noise",
    "compressor noise",
    "road dust",
    "haul route concerns",
    "road damage",
    "containment pond",
    "pond smell",
    "wastewater odor",
    "produced water",
     "public opposition",
    "public objected",
    "resident opposition",
    "neighbors objected",
    "citizens objected",
    "citizens opposed",
    "air pollution concerns",
    "voc emissions",
    "volatile organic compounds",
    "nuisance odor",
    "strong odor",
    "foul smell",
    "sulfur smell",
    "chemical exposure",
    "dust mitigation",
    "road maintenance concerns",
    "health concerns",
    "water contamination concerns",
    "groundwater concerns",
    "landowner concerns",
    "safety concerns",
    "fire concerns",
    "noise concerns",
    "vibration concerns"
]

LOCATIONS = [
    "Duchesne",
    "Roosevelt",
    "Myton",
    "Fruitland",
    "Bluebell",
    "Altamont",
    "Tabiona",
    "Neola",
    "Vernal",
    "Uintah",
    "Uintah Basin",
    "Ouray",
    "Bonanza",
    "Whiterocks",
    "Lapoint",
    "Wells Draw",
    "Nine Mile",
    "Blue Bench",
]

TEXT_EXTS = {".txt", ".html", ".md", ".json", ".csv"}

EXCLUDE_DIRS = [
    "archive/data",
    "archive/sources/complaint_records",
    "archive/documentation",
    "archive/scripts",
    "__pycache__",
    "archive/sources/deq_2006_2015_records",
    "archive/sources/deq_2016_2019_records",
    "archive/sources/deq_records",
    "archive/data/deq_environmental_incidents_basin.json"
]


def clean(s):
    return re.sub(r"\s+", " ", s).strip()


def get_snippet(text, idx, window=450):
    return clean(text[max(0, idx - window) : min(len(text), idx + window)])


rows = []

fEXCLUDE_DIRS = [
    "archive/data",
    "archive/sources/complaint_records",
    "archive/documentation",
    "archive/scripts",
    "archive/__pycache__",
]

files = []

for p in ARCHIVE.rglob("*"):
    if not p.is_file():
        continue

    if p.suffix.lower() not in TEXT_EXTS:
        continue

    path_str = str(p.relative_to(ROOT)).replace("\\", "/")

    if any(bad in path_str for bad in EXCLUDE_DIRS):
        continue

    files.append(p)

print("Scanning files:", len(files))

for path in files:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue

    low = text.lower()

    matched_locations = [loc for loc in LOCATIONS if loc.lower() in low]
    if not matched_locations:
        continue

    for phrase in HIGH_CONFIDENCE_PHRASES:
        idx = low.find(phrase.lower())
        if idx == -1:
            continue

        rows.append(
            {
                "review_status": "needs_human_review",
                "source_file": str(path.relative_to(ROOT)).replace("\\", "/"),
                "matched_phrase": phrase,
                "locations": "; ".join(sorted(set(matched_locations))),
                "snippet": get_snippet(text, idx),
            }
        )

# Basic dedupe
seen = set()
deduped = []
for r in rows:
    key = (r["source_file"], r["matched_phrase"], r["snippet"][:180])
    if key in seen:
        continue
    seen.add(key)
    deduped.append(r)

with open(OUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "review_status",
            "source_file",
            "matched_phrase",
            "locations",
            "snippet",
        ],
    )
    writer.writeheader()
    writer.writerows(deduped)

print("Candidate complaint hits:", len(deduped))
print("Output:", OUT)
