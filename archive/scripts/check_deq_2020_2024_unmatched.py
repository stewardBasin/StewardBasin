import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JSON_PATH = ROOT / "archive" / "data" / "deq_environmental_incidents_basin.json"
PDF_DIR = ROOT / "archive" / "sources" / "deq_2020_2024_pdfs"

records = json.load(open(JSON_PATH, encoding="utf-8"))

pdf_report_numbers = set()
for pdf in PDF_DIR.glob("*.pdf"):
    report = pdf.stem.split("_Report_")[-1]
    pdf_report_numbers.add(report)

print("PDF report numbers:", len(pdf_report_numbers))
print("Records with archive_pdf_path:", sum(1 for r in records if r.get("archive_pdf_path")))

print("\nUnmatched 2020-2024 records with real numeric report IDs:")
for r in records:
    rid = str(r.get("derrid") or r.get("id") or "")
    year_text = str(r.get("date_discovered") or r.get("date") or "")
    if rid.isdigit() and rid in pdf_report_numbers and not r.get("archive_pdf_path"):
        print(rid, r.get("date_discovered"), r.get("county"), r.get("title_eventname") or r.get("name"))