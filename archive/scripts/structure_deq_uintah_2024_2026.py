import os
import re
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RAW_FILE = os.path.join(BASE_DIR, "data", "deq_uintah_2024_2026_raw.json")
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "deq_uintah_2024_2026_structured.json")


def first_match(pattern, text):
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else None


def clean_spaces(value):
    if not value:
        return None
    return re.sub(r"\s+", " ", value).strip()


def to_iso_date(value):
    if not value:
        return None

    match = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", value)
    if not match:
        return None

    try:
        return datetime.strptime(match.group(1), "%m/%d/%Y").strftime("%Y-%m-%d")
    except ValueError:
        return None


def parse_lon_lat(value):
    if not value:
        return None, None, None

    nums = re.findall(r"-?\d+\.\d+", value)

    if len(nums) < 2:
        return None, None, None

    original_lng = float(nums[0])
    lat = float(nums[1])

    lng = original_lng
    correction_note = None

    # Utah longitudes should be negative.
    if lng > 0 and 39 <= lat <= 42:
        lng = -lng
        correction_note = (
            f"Source PDF appears to omit negative longitude. "
            f"Original: {original_lng}, {lat}. "
            f"Corrected: {lng}, {lat}."
        )

    return lng, lat, correction_note


def get_record_id_from_filename(filename):
    match = re.search(r"(500[a-zA-Z0-9]+)", filename)
    return match.group(1) if match else None


def classify_incident(title, summary, chemicals):
    blob = " ".join([title or "", summary or "", chemicals or ""]).lower()

    if "produced water" in blob or "production water" in blob:
        return "Produced Water Release"
    if "injection water" in blob or "treated injection water" in blob:
        return "Treated Injection Water Release"
    if "crude oil" in blob or "oil spill" in blob:
        return "Oil / Petroleum Release"
    if (
        "diesel" in blob
        or "gasoline" in blob
        or "fuel" in blob
        or "hydraulic oil" in blob
    ):
        return "Fuel / Oil Release"
    if "sewage" in blob or "sanitary" in blob or "wastewater" in blob:
        return "Wastewater / Sewage Release"
    if "hydrogen sulfide" in blob or "h2s" in blob:
        return "H2S / Air Release"

    return "DEQ Environmental Incident"


with open(RAW_FILE, "r", encoding="utf-8") as file:
    raw_records = json.load(file)

structured = []

for raw in raw_records:
    text = raw.get("text", "")
    source_file = raw.get("source_file")

    report_number = first_match(r"Report Number:\s*([0-9]+)", text)

    title = first_match(
        r"ENVIRONMENTAL INCIDENT REPORT\s*[-–]\s*(.*?)\n",
        text,
    )

    date_reported_raw = first_match(r"Date/Time Reported:\s*([^\n]+)", text)
    date_discovered_raw = first_match(r"Date\s*&\s*Time\s*Discovered:\s*([^\n]+)", text)

    county = first_match(r"County:\s*([A-Z]+)", text)
    nearest_city = first_match(r"Nearest Town:\s*(.*?)\s*County:", text)

    utm = first_match(r"UTM:\s*(.*?)\s*Land Owner:", text)
    lon_lat_raw = first_match(r"Longitude,\s*Latitude:\s*([^\n]+)", text)
    lng, lat, coordinate_correction_note = parse_lon_lat(lon_lat_raw)

    summary = first_match(
        r"INCIDENT SUMMARY\s*(.*?)\s*CHEMICALS REPORTED",
        text,
    )

    chemicals = first_match(
        r"CHEMICALS REPORTED\s*(.*?)\s*IMPACTED MEDIA",
        text,
    )

    impacted_media = first_match(
        r"IMPACTED MEDIA\s*(.*?)\s*NOTIFICATIONS MADE",
        text,
    )

    incident_type = classify_incident(title, summary, chemicals)
    record_id = get_record_id_from_filename(source_file)

    record = {
        "the_geom": (
            {
                "type": "Point",
                "coordinates": [lng, lat],
            }
            if lng is not None and lat is not None
            else None
        ),
        "objectid": None,
        "sitedesc": "Environmental Incidents",
        "id": report_number,
        "name": clean_spaces(title) or f"DEQ Incident {report_number}",
        "city": clean_spaces(nearest_city),
        "type": (
            f"Environmental Incidents - {report_number}"
            if report_number
            else "Environmental Incidents"
        ),
        "enviroapplabel": (
            f"Environmental Incidents - {report_number}"
            if report_number
            else "Environmental Incidents"
        ),
        "enviroappsymbol": "n/a",
        "county": clean_spaces(county) or "UINTAH",
        "date_discovered_for_filter": (
            to_iso_date(date_discovered_raw) + "T00:00:00.000Z"
            if to_iso_date(date_discovered_raw)
            else None
        ),
        "map_label": (
            f"Environmental Incidents - {report_number}"
            if report_number
            else "Environmental Incidents"
        ),
        "responsible_party": None,
        "address_location": None,
        "incident_summary": clean_spaces(summary),
        "date_discovered": None,
        "derrid": report_number,
        "nearest_city": clean_spaces(nearest_city),
        "title_eventname": clean_spaces(title) or f"DEQ Incident {report_number}",
        "source": "Utah DEQ Environmental Incident Report",
        "source_file": source_file,
        "source_record_id": record_id,
        "source_pdf_url": (
            f"https://deqspillsps.deq.utah.gov/apex/CaseToPDF?id={record_id}"
            if record_id
            else None
        ),
        "date_reported_raw": clean_spaces(date_reported_raw),
        "date_discovered_raw": clean_spaces(date_discovered_raw),
        "date_reported": to_iso_date(date_reported_raw),
        "date_discovered_iso": to_iso_date(date_discovered_raw),
        "longitude_latitude_raw": clean_spaces(lon_lat_raw),
        "coordinate_correction_note": coordinate_correction_note,
        "coordinate_source_value_preserved": clean_spaces(lon_lat_raw),
        "utm": clean_spaces(utm),
        "chemicals_reported": clean_spaces(chemicals),
        "impacted_media": clean_spaces(impacted_media),
        "incident_category": incident_type,
        "review_status": "auto_extracted",
    }

    structured.append(record)

with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
    json.dump(structured, file, indent=2)

print()
print("======================================")
print("DEQ UINTAH STRUCTURED JSON CREATED")
print("======================================")
print(f"Records: {len(structured)}")
print(f"Saved: {OUTPUT_FILE}")

with_coords = [
    r for r in structured if r.get("the_geom") and r["the_geom"].get("coordinates")
]

print(f"Records with coordinates: {len(with_coords)}")
