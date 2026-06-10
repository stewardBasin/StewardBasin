import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
JSON_PATH = ROOT / "archive" / "data" / "deq_environmental_incidents_basin.json"

BACKUP = JSON_PATH.with_name(
    f"deq_environmental_incidents_basin_before_pdf_enrichment_{datetime.now():%Y%m%d_%H%M%S}.json"
)
shutil.copyfile(JSON_PATH, BACKUP)

records = json.load(open(JSON_PATH, encoding="utf-8"))


def clean(value):
    value = str(value or "").strip()
    value = re.sub(r"\s+", " ", value)
    return value


def extract_text(pdf_path):
    reader = PdfReader(str(pdf_path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def after_label(text, label):
    m = re.search(rf"{re.escape(label)}\s*:?\s*\n\s*(.+)", text, re.I)
    return clean(m.group(1)) if m else ""


updated = 0
missing_pdf = 0

for r in records:
    rel_pdf = r.get("archive_pdf_path")
    if not rel_pdf:
        continue

    pdf_path = ROOT / rel_pdf
    if not pdf_path.exists():
        missing_pdf += 1
        continue

    text = extract_text(pdf_path)

    # Responsible party section
    resp_name = ""
    m = re.search(
        r"RESPONSIBLE PARTY\s+Name:\s*\n\s*(.+?)(?:\nPhone:|\nAddress:|\nEmail:|\nINCIDENT LOCATION)",
        text,
        re.I | re.S,
    )
    if m:
        resp_name = clean(m.group(1))

    # Reporting party company, useful fallback
    company = after_label(text, "Company")

    # PDF title/report number
    title = ""
    m = re.search(r"ENVIRONMENTAL INCIDENT REPORT\s*-\s*(.+)", text, re.I)
    if m:
        title = clean(m.group(1))

    report_num = ""
    m = re.search(r"Report Number\s*:?\s*(\d+)", text, re.I)
    if m:
        report_num = m.group(1)

    nearest_town = after_label(text, "Nearest Town")
    county = after_label(text, "County")

    changed = False

    if resp_name and resp_name.lower() not in ["unknown", "n/a"]:
        r["pdf_responsible_party"] = resp_name
        changed = True

    if company and company.lower() not in ["unknown", "n/a"]:
        r["pdf_company"] = company
        changed = True

    if title:
        r["pdf_title"] = title
        changed = True

    if report_num:
        r["pdf_report_number"] = report_num
        changed = True

    if nearest_town:
        r["pdf_nearest_town"] = nearest_town
        changed = True

    if county:
        r["pdf_county"] = county
        changed = True

    if changed:
        updated += 1

json.dump(records, open(JSON_PATH, "w", encoding="utf-8"), indent=2)

print("Backup:", BACKUP)
print("Records enriched:", updated)
print("Missing PDFs:", missing_pdf)