import json
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "archive" / "data"
JSON_PATH = DATA / "deq_environmental_incidents_basin.json"
PDF_DIR = ROOT / "archive" / "sources" / "deq_2020_2024_pdfs"

BACKUP = DATA / f"deq_environmental_incidents_basin_before_sequence_pdf_link_{datetime.now():%Y%m%d_%H%M%S}.json"
shutil.copyfile(JSON_PATH, BACKUP)

records = json.load(open(JSON_PATH, encoding="utf-8"))

pdfs = sorted(PDF_DIR.glob("*.pdf"), key=lambda p: p.name.lower())

fake_records = [
    r for r in records
    if str(r.get("derrid", "")).startswith(("duchesne_2020_2024_", "uintah_2020_2024_"))
]

fake_records.sort(key=lambda r: str(r.get("derrid", "")))

print("PDFs:", len(pdfs))
print("Fake 2020-2024 records:", len(fake_records))

linked = 0

for record, pdf in zip(fake_records, pdfs):
    record["archive_pdf_path"] = str(pdf.relative_to(ROOT)).replace("\\", "/")
    record["source_label"] = "Archived Utah DEQ incident report PDF"
    linked += 1

json.dump(records, open(JSON_PATH, "w", encoding="utf-8"), indent=2)

print("Backup:", BACKUP)
print("Linked by sequence:", linked)