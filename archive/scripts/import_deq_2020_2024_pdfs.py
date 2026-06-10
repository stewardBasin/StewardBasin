import json
import re
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "archive" / "data"

SOURCE_ZIP_DIR = Path(
    r"C:\Users\Annie\OneDrive\Desktop\2020-2024 Uintah and Duchesne enviroIncidentDatabase"
)

PDF_OUT = ROOT / "archive" / "sources" / "deq_2020_2024_pdfs"
PDF_OUT.mkdir(parents=True, exist_ok=True)

MAIN_JSON = DATA / "deq_environmental_incidents_basin.json"
BACKUP = (
    DATA
    / f"deq_environmental_incidents_basin_before_2020_2024_pdf_import_{datetime.now():%Y%m%d_%H%M%S}.json"
)

shutil.copyfile(MAIN_JSON, BACKUP)

records = json.load(open(MAIN_JSON, encoding="utf-8"))

pdf_lookup = {}

for zip_path in SOURCE_ZIP_DIR.glob("*.zip"):
    print("Reading:", zip_path.name)

    with zipfile.ZipFile(zip_path, "r") as z:
        for member in z.namelist():
            if not member.lower().endswith(".pdf"):
                continue

            original_name = Path(member).name

            match = re.search(r"Report_(\d+)\.pdf$", original_name, re.I)
            if not match:
                print("  Could not find report number:", original_name)
                continue

            report_number = match.group(1)

            clean_name = original_name.replace(" ", "_")
            out_path = PDF_OUT / clean_name

            if not out_path.exists():
                with z.open(member) as src, open(out_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)

            pdf_lookup[report_number] = str(out_path.relative_to(ROOT)).replace(
                "\\", "/"
            )

print("PDFs found:", len(pdf_lookup))

updated = 0

for record in records:
    report_id = str(record.get("derrid") or record.get("id") or "")

    if report_id in pdf_lookup:
        record["archive_pdf_path"] = pdf_lookup[report_id]
        record["source_label"] = "Archived Utah DEQ incident report PDF"
        updated += 1

json.dump(records, open(MAIN_JSON, "w", encoding="utf-8"), indent=2)

print("Backup:", BACKUP)
print("Records updated:", updated)
print("PDFs copied to:", PDF_OUT)
