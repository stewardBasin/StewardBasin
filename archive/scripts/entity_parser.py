import os
import json
import re
from datetime import datetime

# =========================
# PATHS
# =========================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

TEXT_FOLDER = os.path.join(BASE_DIR, "extracted_text")
DATA_FOLDER = os.path.join(BASE_DIR, "data")
ENTITY_FILE = os.path.join(DATA_FOLDER, "entities.json")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "entity_mentions")

MASTER_OUTPUT = os.path.join(DATA_FOLDER, "entity_findings.json")
SUMMARY_OUTPUT = os.path.join(DATA_FOLDER, "entity_summary.json")

os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# =========================
# SETTINGS
# =========================

MAX_MATCHES_PER_FILE = 5
SNIPPET_WINDOW = 500

# =========================
# LOAD ENTITIES
# =========================

with open(ENTITY_FILE, "r", encoding="utf-8") as file:
    entities = json.load(file)

# =========================
# TEXT FILES
# =========================

text_files = [
    file for file in os.listdir(TEXT_FOLDER)
    if file.lower().endswith(".txt")
]

print("\n====================")
print("ENTITY PARSER STARTED")
print("====================")
print(f"Text files found: {len(text_files)}")
print(f"Entities loaded: {len(entities)}")

# =========================
# HELPERS
# =========================

def get_snippet(text, index, window=SNIPPET_WINDOW):
    start = max(0, index - window)
    end = min(len(text), index + window)
    return text[start:end].replace("\n", " ").strip()


def safe_filename(name):
    return (
        name.replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
        .replace("&", "and")
        .replace(".", "")
        .replace(",", "")
        .replace(":", "")
        .replace(";", "")
    )


def extract_year(filename, text):
    filename_match = re.search(
        r"(19\d{2}|20\d{2})",
        filename
    )

    if filename_match:
        return filename_match.group(1)

    text_match = re.search(
        r"(19\d{2}|20\d{2})",
        text[:3000]
    )

    if text_match:
        return text_match.group(1)

    return "Unknown"


def guess_county(text):
    lower = text.lower()

    if "duchesne" in lower:
        return "Duchesne"

    if (
        "uintah" in lower
        or "vernal" in lower
        or "uinta basin" in lower
        or "uintah basin" in lower
    ):
        return "Uintah / Uinta Basin"

    return "Unknown"


def make_match_id(entity_name, source_file, index):
    clean_entity = safe_filename(entity_name)
    clean_file = source_file.replace(".txt", "")
    return f"{clean_entity}__{clean_file}__{index}"


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as output:
        json.dump(data, output, indent=2)


# =========================
# SEARCH ENTITIES
# =========================

master_results = []
summary = {}

for entity in entities:

    entity_name = entity.get("name", "").strip()
    entity_type = entity.get("type", "Unknown")

    if not entity_name:
        continue

    print("\n====================")
    print(f"SEARCHING: {entity_name}")
    print("====================")

    matches = []

    for text_file in text_files:

        file_path = os.path.join(TEXT_FOLDER, text_file)

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                text = file.read()

            lower_text = text.lower()
            search_name = entity_name.lower()

            start_index = 0
            match_count = 0

            while match_count < MAX_MATCHES_PER_FILE:

                index = lower_text.find(search_name, start_index)

                if index == -1:
                    break

                year = extract_year(text_file, text)
                county = guess_county(text)
                snippet = get_snippet(text, index)

                match = {
                    "id": make_match_id(entity_name, text_file, index),
                    "entity": entity_name,
                    "type": entity_type,
                    "year": year,
                    "county": county,
                    "source_file": text_file,
                    "snippet": snippet,
                    "character_index": index,
                    "date_found": "",
                    "lat": "",
                    "lng": "",
                    "map_ready": False,
                    "review_status": "needs_review",
                    "created_at": datetime.now().isoformat()
                }

                matches.append(match)
                master_results.append(match)

                if entity_name not in summary:
                    summary[entity_name] = {
                        "type": entity_type,
                        "total_matches": 0,
                        "years": {},
                        "counties": {}
                    }

                summary[entity_name]["total_matches"] += 1
                summary[entity_name]["years"][year] = (
                    summary[entity_name]["years"].get(year, 0) + 1
                )
                summary[entity_name]["counties"][county] = (
                    summary[entity_name]["counties"].get(county, 0) + 1
                )

                print(f"FOUND: {entity_name} | {year} | {county} | {text_file}")

                match_count += 1
                start_index = index + len(search_name)

        except Exception as e:
            print(f"FAILED: {text_file}")
            print(e)

    # =========================
    # SAVE ENTITY-SPECIFIC FILE
    # =========================

    output_path = os.path.join(
        OUTPUT_FOLDER,
        f"{safe_filename(entity_name)}.json"
    )

    save_json(output_path, matches)

    print(f"SAVED ENTITY FILE: {output_path}")
    print(f"Matches for {entity_name}: {len(matches)}")

    # =========================
    # AUTOSAVE MASTER
    # =========================

    save_json(MASTER_OUTPUT, master_results)
    save_json(SUMMARY_OUTPUT, summary)

# =========================
# FINAL SAVE
# =========================

save_json(MASTER_OUTPUT, master_results)
save_json(SUMMARY_OUTPUT, summary)

# =========================
# DONE
# =========================

print("\n====================")
print("ENTITY PARSE COMPLETE")
print("====================")
print(f"Total matches: {len(master_results)}")
print(f"Entity files saved to: {OUTPUT_FOLDER}")
print(f"Master file saved to: {MASTER_OUTPUT}")
print(f"Summary file saved to: {SUMMARY_OUTPUT}")