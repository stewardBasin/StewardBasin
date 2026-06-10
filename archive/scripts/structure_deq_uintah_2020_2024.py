import os
import re
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RAW_FILE = os.path.join(BASE_DIR, "data", "deq_uintah_2020_2024_raw.txt")
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "deq_uintah_2020_2024.json")


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

lines = [line.strip() for line in raw.splitlines() if line.strip()]

records = []
date_re = re.compile(r"^\d{1,2}/\d{1,2}/\d{4}$")

i = 0
while i < len(lines):
    line = lines[i]

    if not date_re.match(line):
        i += 1
        continue

    date_text = line

    parts = []
    j = i + 1

    while j < len(lines):
        value = lines[j].strip()

        if date_re.match(value):
            break

        if value.lower() in ["details", "map", "d/l", "start", "end"]:
            j += 1
            continue

        if value.startswith("Utah Department of Environmental Quality"):
            break

        if value not in ["Â", "Â Â Â Â", "- Please Select -"]:
            parts.append(value)

        if len(parts) >= 4:
            break

        j += 1

    company = parts[0] if len(parts) > 0 else None
    material = parts[1] if len(parts) > 1 else None
    media = parts[2] if len(parts) > 2 else None
    city = parts[3] if len(parts) > 3 else None

    date_iso = iso_date(date_text)
    category = classify(" ".join([material or "", media or ""]))

    title = " - ".join(
        part
        for part in [city, material, company]
        if part and part != "- Please Select -"
    )

    record_id = f"uintah_2020_2024_{len(records) + 1:03d}"

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
            "county": "UINTAH",
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
            "source": "Utah DEQ incident listing, Uintah 2020-2024",
            "source_file": "deq_uintah_2020_2024_raw.txt",
            "incident_category": category,
            "review_status": "summary_listing_no_coordinates",
        }
    )

    i = j

with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
    json.dump(records, file, indent=2)

print("Structured Uintah 2020-2024 records:", len(records))
print("Saved:", OUTPUT_FILE)
