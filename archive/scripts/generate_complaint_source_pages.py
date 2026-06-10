import json
import html
import re
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JSON_PATH = ROOT / "archive" / "data" / "complaints.json"

OUT = ROOT / "archive" / "sources" / "complaint_records"
OUT.mkdir(parents=True, exist_ok=True)

BACKUP = JSON_PATH.with_name(
    f"complaints_before_source_pages_{datetime.now():%Y%m%d_%H%M%S}.json"
)
shutil.copyfile(JSON_PATH, BACKUP)

records = json.load(open(JSON_PATH, encoding="utf-8"))


def esc(v):
    return html.escape(str(v or "Unknown"))


def slugify(value):
    value = str(value or "complaint").lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")[:80]


updated = 0

for i, r in enumerate(records, start=1):
    rid = r.get("id") or r.get("complaint_id") or f"complaint_{i:03d}"
    filename = f"{i:03d}_{slugify(rid)}.html"
    out_path = OUT / filename

    title = (
        r.get("title")
        or r.get("type")
        or r.get("category")
        or "Complaint / Public Record"
    )
    date = r.get("date") or r.get("year") or "Unknown"
    category = r.get("category") or r.get("type") or "Unknown"
    county = r.get("county") or "Unknown"
    location = (
        r.get("location")
        or r.get("nearest_city")
        or r.get("city")
        or "County-level record; no address provided"
    )
    source = r.get("source") or "Parsed public record"
    text = r.get("description") or r.get("summary") or r.get("text") or ""

    original_url = r.get("source_url") or r.get("url") or r.get("document_url") or ""

    original_link = ""
    if original_url:
        original_link = f"""
        <p>
          <a href="{esc(original_url)}" target="_blank" rel="noopener">
            View original source document
          </a>
        </p>
        """

    page = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>{esc(title)}</title>
  <style>
    body {{ font-family: Georgia, serif; max-width: 850px; margin: 40px auto; line-height: 1.45; }}
    h1 {{ color: #4d6548; }}
    .meta {{ background: #f7f1e8; padding: 16px; border-radius: 10px; }}
    .summary {{ white-space: pre-wrap; margin-top: 20px; }}
  </style>
</head>
<body>
  <h1>{esc(title)}</h1>

  <div class="meta">
    <p><strong>Record #:</strong> {esc(rid)}</p>
    <p><strong>Date / Year:</strong> {esc(date)}</p>
    <p><strong>Category:</strong> {esc(category)}</p>
    <p><strong>County:</strong> {esc(county)}</p>
    <p><strong>Location:</strong> {esc(location)}</p>
    <p><strong>Source:</strong> {esc(source)}</p>
  </div>

  <h2>Complaint / Public Record Text</h2>
  <div class="summary">{esc(text)}</div>

  <h2>Source Information</h2>
  <p><strong>Source type:</strong> Parsed public record / public meeting record.</p>
  <p><strong>Source file:</strong> {esc(r.get("source_file"))}</p>
  {original_link}
</body>
</html>
"""

    out_path.write_text(page, encoding="utf-8")
    r["local_source_path"] = str(out_path.relative_to(ROOT)).replace("\\", "/")
    updated += 1

json.dump(records, open(JSON_PATH, "w", encoding="utf-8"), indent=2)

print("Backup:", BACKUP)
print("Complaint source pages created:", updated)
print("Output:", OUT)
