import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEXT_FOLDER = os.path.join(BASE_DIR, "extracted_text", "deq_duchesne_2024_2026")

OUTPUT_FILE = os.path.join(BASE_DIR, "data", "deq_duchesne_2024_2026_raw.json")

records = []

for filename in os.listdir(TEXT_FOLDER):

    if not filename.endswith(".txt"):
        continue

    path = os.path.join(TEXT_FOLDER, filename)

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()

    records.append({"source_file": filename, "text": text})

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(records, f, indent=2)

print()
print("===================================")
print("DEQ DUCHESNE RAW JSON CREATED")
print("===================================")
print(f"Records: {len(records)}")
print(f"Saved: {OUTPUT_FILE}")
