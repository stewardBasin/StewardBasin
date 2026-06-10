import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

SOURCE_FILE = BASE_DIR / "data" / "verified_complaint_candidates.json"
OUTPUT_FILE = BASE_DIR / "data" / "verified_complaint_location_review.json"

LOCATION_PATTERNS = [
    r"\bnear\s+([A-Z][A-Za-z0-9\s\-\/]+)",
    r"\bsouth of\s+([A-Z][A-Za-z0-9\s\-\/]+)",
    r"\bnorth of\s+([A-Z][A-Za-z0-9\s\-\/]+)",
    r"\beast of\s+([A-Z][A-Za-z0-9\s\-\/]+)",
    r"\bwest of\s+([A-Z][A-Za-z0-9\s\-\/]+)",
    r"\bin the\s+([A-Z][A-Za-z0-9\s\-\/]+ area)",
    r"\b([A-Z][A-Za-z0-9\s\-\/]+ Road)",
    r"\b([A-Z][A-Za-z0-9\s\-\/]+ Canyon)",
    r"\b([A-Z][A-Za-z0-9\s\-\/]+ Creek)",
    r"\b(Bluebell|Roosevelt|Duchesne|Myton|Altamont|Tabiona|Vernal|Naples|Jensen|Randlett|Ouray|Ballard|Lapoint|Arcadia|Blue Bench|Pleasant Valley|Lamb Road|Higley)",
]

with open(SOURCE_FILE, "r", encoding="utf-8") as f:
    records = json.load(f)

review = []

for r in records:
    desc = r.get("description", "") or ""
    guesses = []

    for pattern in LOCATION_PATTERNS:
        for match in re.findall(pattern, desc):
            if isinstance(match, tuple):
                match = " ".join(m for m in match if m)
            guesses.append(str(match).strip())

    guesses = sorted(set(g for g in guesses if len(g) > 2))

    review.append(
        {
            "id": r.get("id"),
            "type": r.get("type"),
            "date": r.get("date"),
            "year": r.get("year"),
            "county": r.get("county"),
            "source_file": r.get("source_file"),
            "source": r.get("source"),
            "description": desc,
            "location_clues_found": guesses,
            "suggested_location_label": r.get("location_label") or "",
            "suggested_lat": r.get("lat") or "",
            "suggested_lng": r.get("lng") or "",
            "location_confidence": r.get("location_confidence")
            or "needs_location_review",
            "review_notes": "",
        }
    )

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(review, f, indent=2)

print("Location review records:", len(review))
print("Saved:", OUTPUT_FILE)
