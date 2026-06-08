import os
import re
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RAW_FILE = os.path.join(BASE_DIR, "data", "deq_duchesne_2020_2024_raw.txt")
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "deq_duchesne_2020_2024.json")


def classify(material):
    text = (material or "").lower()

    if "hydrogen sulfide" in text or "h2s" in text:
        return "H2S / Air Release"
    if "natural gas" in text or "nitrogen" in text or "outdoor air" in text:
        return "H2S / Air Release"
    if "production water" in text or "produced water" in text:
        return "Produced Water Release"
    if "injection water" in text:
        return "Treated Injection Water Release"
    if "crude oil" in text or "petroleum" in text:
        return "Oil / Petroleum Release"
    if "diesel" in text or "fuel" in text or "antifreeze" in text:
        return "Fuel Release"
    if "sewage" in text or "wastewater" in text:
        return "Wastewater / Sewage Release"
    return "DEQ Environmental Incident"


def iso_date(date_text):
    try:
        return datetime.strptime(date_text, "%m/%d/%Y").strftime("%Y-%m-%d")
    except Exception:
        return None


with open(RAW_FILE, "r", encoding="utf-8", errors="ignore") as file:
    raw = file.read()

# Split on date lines like 1/7/2021
matches = list(re.finditer(r"(?m)^(\d{1,2}/\d{1,2}/\d{4})\s*$", raw))

records = []

for i, match in enumerate(matches):
    date_text = match.group(1)
    start = match.end()
    end = matches[i + 1].start() if i + 1 < len(matches) else len(raw)

    block = raw[start:end]
    lines = [
        line.strip()
        for line in block.splitlines()
        if line.strip() and line.strip().lower() not in ["details", "map"]
    ]

    if not lines:
        continue

    # These rows are from a DEQ listing table:
    # Company | Material | Media | City
    row = re.split(r"\t+|\s{2,}", lines[0])
    row = [part.strip() for part in row if part.strip()]

    company = row[0] if len(row) > 0 else None
    material = row[1] if len(row) > 1 else None
    media = row[2] if len(row) > 2 else None
    city = row[3] if len(row) > 3 else None

    date_iso = iso_date(date_text)
    category = classify(" ".join([material or "", media or ""]))

    title = " - ".join(
        part
        for part in [
            city,
            material,
            company,
        ]
        if part and part != "- Please Select -"
    )

    record_id = f"duchesne_2020_2024_{len(records) + 1:03d}"

    records.append(
        {
            "the_geom": None,
            "objectid": None,
            "sitedesc": "Environmental Incidents",
            "id": record_id,
            "name": title or f"DEQ Incident {date_text}",
            "city": city,
            "type": f"Environmental Incidents - {record_id}",
            "enviroapplabel": f"Environmental Incidents - {record_id}",
            "enviroappsymbol": "n/a",
            "county": "DUCHESNE",
            "date_discovered_for_filter": (
                f"{date_iso}T00:00:00.000Z" if date_iso else None
            ),
            "map_label": f"Environmental Incidents - {record_id}",
            "responsible_party": company,
            "address_location": None,
            "incident_summary": f"{material or 'Unknown material'} reported impacting {media or 'unknown media'} near {city or 'unknown location'}.",
            "date_discovered": date_text,
            "derrid": record_id,
            "nearest_city": city,
            "title_eventname": title or f"DEQ Incident {date_text}",
            "source": "Utah DEQ incident listing, Duchesne 2020-2024",
            "source_file": "deq_duchesne_2020_2024_raw.txt",
            "incident_category": category,
            "review_status": "summary_listing_no_coordinates",
        }
    )

with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
    json.dump(records, file, indent=2)

print("Structured 2020-2024 records:", len(records))
print("Saved:", OUTPUT_FILE)
