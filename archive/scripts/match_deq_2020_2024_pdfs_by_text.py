import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "archive" / "data"
JSON_PATH = DATA / "deq_environmental_incidents_basin.json"
PDF_DIR = ROOT / "archive" / "sources" / "deq_2020_2024_pdfs"

BACKUP = (
    DATA
    / f"deq_environmental_incidents_basin_before_text_pdf_match_{datetime.now():%Y%m%d_%H%M%S}.json"
)
shutil.copyfile(JSON_PATH, BACKUP)

records = json.load(open(JSON_PATH, encoding="utf-8"))


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", str(s or "").lower()).strip()


def get_after(text, label):
    # captures the line after a label like "County:"
    m = re.search(rf"{re.escape(label)}\s*:?\s*\n\s*(.+)", text, re.I)
    return m.group(1).strip() if m else ""


def get_pdf_text(pdf_path):
    try:
        reader = PdfReader(str(pdf_path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        print("PDF read failed:", pdf_path.name, e)
        return ""


pdfs = []

for pdf in PDF_DIR.glob("*.pdf"):
    text = get_pdf_text(pdf)

    report_number = ""
    m = re.search(r"Report Number\s+(\d+)", text, re.I)
    if m:
        report_number = m.group(1)

    date = get_after(text, "Date & Time Discovered").split()[0]
    county = get_after(text, "County")
    town = get_after(text, "Nearest Town")
    company = get_after(text, "Company")
    responsible = get_after(text, "Name")

    title = ""
    m = re.search(r"ENVIRONMENTAL INCIDENT REPORT\s*-\s*(.+)", text, re.I)
    if m:
        title = m.group(1).strip()

    pdfs.append(
        {
            "path": pdf,
            "rel": str(pdf.relative_to(ROOT)).replace("\\", "/"),
            "report_number": report_number,
            "date": date,
            "county": county,
            "town": town,
            "company": company,
            "responsible": responsible,
            "title": title,
            "search": norm(
                " ".join(
                    [date, county, town, company, responsible, title, report_number]
                )
            ),
        }
    )

print("PDFs indexed:", len(pdfs))

updated = 0
ambiguous = []
unmatched = []

for r in records:
    rid = str(r.get("derrid") or "")

    if not rid.startswith(("duchesne_2020_2024_", "uintah_2020_2024_")):
        continue

    record_date = str(r.get("date_discovered") or r.get("date") or "").strip()
    record_county = str(r.get("county") or "").strip()
    record_city = str(r.get("nearest_city") or r.get("city") or "").strip()
    record_company = str(r.get("responsible_party") or r.get("company") or "").strip()
    record_title = str(
        r.get("title_eventname") or r.get("name") or r.get("title") or ""
    ).strip()

    record_terms = norm(
        " ".join(
            [record_date, record_county, record_city, record_company, record_title]
        )
    )

    candidates = []

    for p in pdfs:
        score = 0

        if record_date and p["date"] == record_date:
            score += 5

        if record_county and norm(record_county) == norm(p["county"]):
            score += 3

        if record_city and norm(record_city) == norm(p["town"]):
            score += 3

        if (
            record_company
            and norm(record_company)
            and norm(record_company) in p["search"]
        ):
            score += 4

        title_words = [w for w in norm(record_title).split() if len(w) >= 4]
        title_hits = sum(1 for w in title_words if w in p["search"])
        score += min(title_hits, 4)

        if score >= 8:
            candidates.append((score, p))

    candidates.sort(key=lambda x: x[0], reverse=True)

    if len(candidates) == 1 or (
        len(candidates) > 1 and candidates[0][0] >= candidates[1][0] + 3
    ):
        best = candidates[0][1]
        r["archive_pdf_path"] = best["rel"]
        r["matched_report_number"] = best["report_number"]
        r["source_label"] = "Archived Utah DEQ incident report PDF"
        updated += 1
    elif candidates:
        ambiguous.append(
            (
                rid,
                record_date,
                record_county,
                record_city,
                record_company,
                record_title,
                [(s, c["path"].name, c["title"]) for s, c in candidates[:3]],
            )
        )
    else:
        unmatched.append(
            (rid, record_date, record_county, record_city, record_company, record_title)
        )

json.dump(records, open(JSON_PATH, "w", encoding="utf-8"), indent=2)

print("Backup:", BACKUP)
print("Updated:", updated)
print("Ambiguous:", len(ambiguous))
print("Unmatched:", len(unmatched))

print("\nSample ambiguous:")
for item in ambiguous[:10]:
    print(item)

print("\nSample unmatched:")
for item in unmatched[:10]:
    print(item)
