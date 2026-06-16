from pathlib import Path
import csv
import re
import hashlib

ROOT = Path(__file__).resolve().parents[3]
ARCHIVE = ROOT / "archive"

OUTDIR = ROOT / "archive/data/deep_mining_review/targeted_entity_clean"
OUTDIR.mkdir(parents=True, exist_ok=True)

OUT = OUTDIR / "targeted_entity_hits_clean.csv"

TEXT_EXTS = {".txt", ".html", ".md", ".json", ".csv"}

TARGET_TERMS = [
    "Energence LLC",
    "Eneregence LLC",
    "Nine Mile LLC",
    "Wells Draw LLC",
    "reWater LLC",
    "Vaibhav Shree LLC",
    "Wasatch Energy",
    "4-C Farms",
    "4 C Farms",
    "4C Farms",
    "4C Ranch",
    "Blue Diamond Proppants",
    "Eastern Duchesne Water District",
    "Duchesne Culinary Water District",
    "Blue Bench landfill",
    "Hancock Cove",
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
    "Hancock Cove",
]

EXCLUDE_DIRS = [
    # generated data / previous mining outputs
    "archive/data",
    "archive/clean",
    "archive/documentation",
    "archive/entity_mentions",
    "archive/entity_text"
    # generated public archive pages
    "archive/sources/complaint_records",
    "archive/sources/deq_2006_2015_records",
    "archive/sources/deq_2016_2019_records",
    "archive/sources/deq_missing_local_records",
    # scripts / cache
    "archive/scripts",
    "__pycache__",
]

EXCLUDE_FILE_CONTAINS = [
    "before_",
    "_backup",
    "backup",
    "archive_integrity_index",
    "deep_mining_keyword_hits",
    "targeted_blue_bench_hits",
    "complaint_candidates_v2",
]


def clean(s):
    return re.sub(r"\s+", " ", s).strip()


def get_snippet(text, idx, window=650):
    return clean(text[max(0, idx - window) : min(len(text), idx + window)])


def normalize_for_hash(s):
    return re.sub(r"\s+", " ", s.lower()).strip()


def fingerprint(source_file, term, snippet):
    raw = f"{source_file}|{term.lower()}|{normalize_for_hash(snippet)[:300]}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def should_skip(path):
    rel = path.relative_to(ROOT)
    rel_posix = rel.as_posix()
    parts = rel.parts
    name = path.name.lower()

    # Skip generated folders by path parts, not fragile string matching
    if "data" in parts and "archive" in parts:
        return True

    if "clean" in parts and "archive" in parts:
        return True

    if "documentation" in parts and "archive" in parts:
        return True

    if "entity_mentions" in parts and "archive" in parts:
        return True

    if "entity_text" in parts and "archive" in parts:
        return True

    if "scripts" in parts and "archive" in parts:
        return True

    if "__pycache__" in parts:
        return True

    # Skip generated public complaint/deq archive pages
    if "sources" in parts and "complaint_records" in parts:
        return True

    if "sources" in parts and "deq_2006_2015_records" in parts:
        return True

    if "sources" in parts and "deq_2016_2019_records" in parts:
        return True

    if "sources" in parts and "deq_missing_local_records" in parts:
        return True

    # Skip backups / generated reports

    if any(
        bad in name
        for bad in [
            "before_",
            "_backup",
            "backup",
            "archive_integrity_index",
            "deep_mining_keyword_hits",
            "targeted_blue_bench_hits",
            "complaint_candidates_v2",
        ]
    ):
        return True

    return False


def source_kind(path):
    rel = str(path.relative_to(ROOT)).replace("\\", "/").lower()

    if "extracted_text" in rel:
        return "extracted_text"
    if "entity_mentions" in rel or "entity_text" in rel:
        return "entity_archive"
    if "meeting_minutes" in rel:
        return "meeting_minutes"
    if "sources" in rel:
        return "source_archive"
    return "other_archive_file"


files = []
for p in ARCHIVE.rglob("*"):

    if not p.is_file():
        continue

    if should_skip(p):
        continue

    files.append(p)

rows = []
seen = set()

print("Scanning files:", len(files))

for path in files:
    rel = str(path.relative_to(ROOT)).replace("\\", "/")

    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue

    low = text.lower()
    matched_locations = [loc for loc in LOCATION_TERMS if loc.lower() in low]

    for term in TARGET_TERMS:
        start = 0

        while True:
            idx = low.find(term.lower(), start)
            if idx == -1:
                break

            snip = get_snippet(text, idx)
            fp = fingerprint(rel, term, snip)

            if fp not in seen:
                seen.add(fp)

                rows.append(
                    {
                        "review_status": "needs_human_review",
                        "source_kind": source_kind(path),
                        "source_file": rel,
                        "matched_term": term,
                        "locations": "; ".join(sorted(set(matched_locations))),
                        "snippet": snip,
                        "dedupe_fingerprint": fp,
                    }
                )

            start = idx + len(term)

with open(OUT, "w", newline="", encoding="utf-8") as f:
    fieldnames = [
        "review_status",
        "source_kind",
        "source_file",
        "matched_term",
        "locations",
        "snippet",
        "dedupe_fingerprint",
    ]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print("Clean targeted hits:", len(rows))
print("Output:", OUT)
