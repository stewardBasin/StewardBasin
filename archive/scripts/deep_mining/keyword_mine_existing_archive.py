from pathlib import Path
import csv
import re
from datetime import datetime

ROOT = Path(__file__).resolve().parents[3]
ARCHIVE = ROOT / "archive"

OUT = ROOT / "archive/data/deep_mining_keyword_hits.csv"

KEYWORDS = [
    "odor",
    "smell",
    "VOC",
    "volatile organic",
    "air quality",
    "chemical smell",
    "hydrogen sulfide",
    "H2S",
    "sour gas",
    "noxious fumes",
    "emissions",
    "flaring",
    "flare noise",
    "compressor noise",
    "dust",
    "road dust",
    "PM10",
    "particulate",
    "truck traffic",
    "haul route",
    "gravel pit",
    "crusher",
    "sand mine",
    "wastewater",
    "pond smell",
    "containment pond",
    "lagoon",
    "reWater",
    "sewage",
    "produced water",
    "public concern",
    "resident concern",
    "citizen concern",
    "public comment",
    "complaint",
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
    "Fruitland",
]

TEXT_EXTS = {".txt", ".html", ".md", ".json", ".csv"}


def clean_text(s):
    return re.sub(r"\s+", " ", s).strip()


def snippet(text, idx, window=220):
    start = max(0, idx - window)
    end = min(len(text), idx + window)
    return clean_text(text[start:end])


rows = []

files = [p for p in ARCHIVE.rglob("*") if p.is_file() and p.suffix.lower() in TEXT_EXTS]

print("Scanning text-like files:", len(files))

for path in files:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue

    low = text.lower()

    matched_locations = [loc for loc in LOCATIONS if loc.lower() in low]
    if not matched_locations:
        continue

    for kw in KEYWORDS:
        pattern = kw.lower()
        idx = low.find(pattern)

        if idx == -1:
            continue

        rows.append(
            {
                "file": str(path.relative_to(ROOT)).replace("\\", "/"),
                "keyword": kw,
                "locations": "; ".join(sorted(set(matched_locations))),
                "snippet": snippet(text, idx),
            }
        )

with open(OUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["file", "keyword", "locations", "snippet"])
    writer.writeheader()
    writer.writerows(rows)

print("Hits:", len(rows))
print("Output:", OUT)
