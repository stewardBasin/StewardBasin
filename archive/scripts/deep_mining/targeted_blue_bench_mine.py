from pathlib import Path
import csv
import re

ROOT = Path(__file__).resolve().parents[3]
ARCHIVE = ROOT / "archive"
OUT = ROOT / "archive/data/deep_mining_review/targeted_blue_bench_hits.csv"
OUT.parent.mkdir(parents=True, exist_ok=True)

TEXT_EXTS = {".txt", ".html", ".md", ".json", ".csv"}

TARGET_TERMS = [
    # Blue Bench / nearby industrial
    "Blue Bench",
    "Blue Bench Road",
    "Blue Bench landfill",
    "landfill odor",
    "4-C Farms",
    "4 C Farms",
    "4-C Farm",
    "4C Farms",
    "4C Ranch",
    "Blue Diamond Proppants",
    "proppants",
    "sand pit",
    "gravel pit",
    "rock crusher",
    "crusher operation",
    "dust control plan",
    "haul road",
    "truck traffic",
    # Water / governance
    "Eastern Duchesne Water District",
    "Duchesne County Water Conservancy District",
    "culinary water district",
    "water district",
    "board of trustees",
    "annexed",
    "annexation",
    # Nine Mile / Wells Draw / reWater
    "reWater",
    "reWater LLC",
    "Wells Draw",
    "Nine Mile",
    "Nine Mile Data Center",
    "Uintah Basin Data Center",
    "produced water disposal",
    "wastewater facility",
    "containment pond",
    "evaporation pond",
    "pond odor",
    "odor complaint",
    "VOC",
    "volatile organic",
    "natural gas power plant",
    "gas fired power plant",
]

LOCATION_TERMS = [
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

EXCLUDE_DIRS = [
    "archive/data/deep_mining_review",
    "archive/data/archive_integrity_index.json",
    "archive/data/deep_mining_keyword_hits.csv",
    "archive/sources/complaint_records",
    "archive/sources/deq_2006_2015_records",
    "archive/sources/deq_2016_2019_records",
    "archive/scripts",
    "__pycache__",
]


def clean(s):
    return re.sub(r"\s+", " ", s).strip()


def get_snippet(text, idx, window=550):
    return clean(text[max(0, idx - window) : min(len(text), idx + window)])


def should_skip(path):
    path_str = str(path.relative_to(ROOT)).replace("\\", "/")
    return any(bad in path_str for bad in EXCLUDE_DIRS)


rows = []

files = []
for p in ARCHIVE.rglob("*"):
    if not p.is_file():
        continue
    if p.suffix.lower() not in TEXT_EXTS:
        continue
    if should_skip(p):
        continue
    files.append(p)

print("Scanning files:", len(files))

for path in files:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue

    low = text.lower()
    matched_locations = [loc for loc in LOCATION_TERMS if loc.lower() in low]

    for term in TARGET_TERMS:
        idx = low.find(term.lower())
        if idx == -1:
            continue

        rows.append(
            {
                "review_status": "needs_human_review",
                "source_file": str(path.relative_to(ROOT)).replace("\\", "/"),
                "matched_term": term,
                "locations": "; ".join(sorted(set(matched_locations))),
                "snippet": get_snippet(text, idx),
            }
        )

# light dedupe
seen = set()
deduped = []
for r in rows:
    key = (r["source_file"], r["matched_term"], r["snippet"][:220])
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
            "matched_term",
            "locations",
            "snippet",
        ],
    )
    writer.writeheader()
    writer.writerows(deduped)

print("Targeted hits:", len(deduped))
print("Output:", OUT)
