import os
import json
import re
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEXT_FOLDER = os.path.join(BASE_DIR, "extracted_text")
DATA_FOLDER = os.path.join(BASE_DIR, "data")
OUTPUT_FOLDER = os.path.join(DATA_FOLDER, "complaint_h2s_findings_by_year")

os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

MASTER_OUTPUT = os.path.join(DATA_FOLDER, "complaint_h2s_findings.json")
SUMMARY_OUTPUT = os.path.join(DATA_FOLDER, "complaint_h2s_summary.json")

REGION_TERMS = [
    "duchesne",
    "uintah",
    "uinta basin",
    "uintah basin",
    "eastern utah",
    "vernal",
    "roosevelt",
    "fruitland",
    "altamont",
    "myton",
    "ballard",
    "fort duchesne"
]

CATEGORIES = {
    "Complaints": [
        "odor complaint",
        "air complaint",
        "emissions complaint",
        "resident complaint",
        "citizen complaint",
        "environmental complaint",
        "complaint investigation",
        "public nuisance"
    ],
    "H2S / Odor": [
        "h2s",
        "hydrogen sulfide",
        "hydrogen sulphide",
        "rotten egg",
        "sulfur odor",
        "sulphur odor",
        "oilfield odor",
        "gas odor"
    ],
    "Ozone / Air Quality": [
        "ozone exceedance",
        "ozone nonattainment",
        "ozone standard",
        "nonattainment",
        "out of attainment",
        "exceedance",
        "pm2.5",
        "pm 2.5",
        "pm10",
        "pm 10",
        "fugitive dust",
        "particulate matter"
    ],
    "VOC / Benzene": [
        "voc exceedance",
        "voc violation",
        "voc complaint",
        "voc monitoring",
        "volatile organic compounds exceedance",
        "volatile organic compounds violation",
        "benzene exceedance",
        "benzene violation",
        "benzene monitoring"
    ],
    "Water / Spill / Contamination": [
        "produced water spill",
        "produced water release",
        "wastewater incident",
        "unauthorized discharge",
        "unauthorized release",
        "water contamination",
        "groundwater contamination",
        "pipeline leak",
        "spill report",
        "release report"
    ],
    "Enforcement / Noncompliance": [
        "notice of violation",
        "noncompliance",
        "compliance order",
        "enforcement action",
        "inspection report",
        "incident report"
    ],
    "Health Impacts": [
        "asthma",
        "copd",
        "respiratory illness",
        "lung disease",
        "headache",
        "hospitalization",
        "emergency room",
        "toxic exposure",
        "environmental exposure"
    ]
}

MAX_SNIPPETS_PER_CATEGORY_PER_FILE = 3


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as output:
        json.dump(data, output, indent=2)


def get_year(filename, text):
    filename_year = re.search(r"(20[0-2][0-9]|19[0-9][0-9])", filename)
    if filename_year:
        return filename_year.group(1)

    text_year = re.search(r"(20[0-2][0-9]|19[0-9][0-9])", text[:3000])
    if text_year:
        return text_year.group(1)

    return "unknown"


def get_snippet(text, index, window=450):
    start = max(0, index - window)
    end = min(len(text), index + window)
    return text[start:end].replace("\n", " ").strip()


def has_region(text):
    lower = text.lower()
    return any(term in lower for term in REGION_TERMS)


def guess_county(text):
    lower = text.lower()

    if "duchesne" in lower:
        return "Duchesne"

    if "uintah" in lower or "uinta basin" in lower or "uintah basin" in lower or "vernal" in lower:
        return "Uintah / Uinta Basin"

    return "Unknown"


def find_category_matches(text, category, keywords):
    lower = text.lower()
    matches = []

    for keyword in keywords:
        keyword_lower = keyword.lower()
        start_index = 0

        while len(matches) < MAX_SNIPPETS_PER_CATEGORY_PER_FILE:
            index = lower.find(keyword_lower, start_index)

            if index == -1:
                break

            matches.append({
                "keyword": keyword,
                "character_index": index,
                "snippet": get_snippet(text, index)
            })

            start_index = index + len(keyword_lower)

        if len(matches) >= MAX_SNIPPETS_PER_CATEGORY_PER_FILE:
            break

    return matches


text_files = [
    file for file in os.listdir(TEXT_FOLDER)
    if file.lower().endswith(".txt")
]

print("\n====================")
print("TARGETED COMPLAINT / H2S PARSER")
print("====================")
print(f"Text files found: {len(text_files)}")

all_findings = []
findings_by_year = {}
summary = {}

processed = 0
skipped_no_region = 0

for text_file in text_files:
    file_path = os.path.join(TEXT_FOLDER, text_file)

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
            text = file.read()

        if not has_region(text):
            skipped_no_region += 1
            continue

        year = get_year(text_file, text)
        county = guess_county(text)

        file_had_match = False

        for category, keywords in CATEGORIES.items():
            matches = find_category_matches(text, category, keywords)

            if not matches:
                continue

            file_had_match = True

            finding = {
                "id": f"{year}__{category.replace(' ', '_').replace('/', '_')}__{text_file}",
                "year": year,
                "category": category,
                "source_file": text_file,
                "county": county,
                "match_count_saved": len(matches),
                "matches": matches,
                "date_found": "",
                "lat": "",
                "lng": "",
                "map_ready": False,
                "review_status": "needs_review",
                "created_at": datetime.now().isoformat()
            }

            all_findings.append(finding)

            if year not in findings_by_year:
                findings_by_year[year] = []

            findings_by_year[year].append(finding)

            if year not in summary:
                summary[year] = {}

            summary[year][category] = summary[year].get(category, 0) + 1

            print(f"FOUND: {year} | {category} | {text_file}")

        processed += 1

        if processed % 25 == 0:
            save_json(MASTER_OUTPUT, all_findings)
            save_json(SUMMARY_OUTPUT, summary)

            for save_year, records in findings_by_year.items():
                save_json(
                    os.path.join(OUTPUT_FOLDER, f"{save_year}.json"),
                    records
                )

            print(f"AUTOSAVED after {processed} files")

    except Exception as e:
        print(f"FAILED: {text_file}")
        print(e)

save_json(MASTER_OUTPUT, all_findings)
save_json(SUMMARY_OUTPUT, summary)

for year, records in findings_by_year.items():
    save_json(
        os.path.join(OUTPUT_FOLDER, f"{year}.json"),
        records
    )

print("\n====================")
print("PARSE COMPLETE")
print("====================")
print(f"Total findings: {len(all_findings)}")
print(f"Skipped no-region files: {skipped_no_region}")
print(f"Master saved to: {MASTER_OUTPUT}")
print(f"Summary saved to: {SUMMARY_OUTPUT}")
print(f"Year files saved to: {OUTPUT_FOLDER}")