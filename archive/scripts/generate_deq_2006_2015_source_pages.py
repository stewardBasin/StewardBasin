import json
import html
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "archive" / "data"
JSON_PATH = DATA / "deq_incidents_pre2016.json"

OUT = ROOT / "archive" / "sources" / "deq_2006_2015_records"
OUT.mkdir(parents=True, exist_ok=True)

BACKUP = (
    DATA
    / f"deq_incidents_pre2016_before_source_pages_{datetime.now():%Y%m%d_%H%M%S}.json"
)
shutil.copyfile(JSON_PATH, BACKUP)

records = json.load(open(JSON_PATH, encoding="utf-8"))


def esc(v):
    return html.escape(str(v or "Unknown"))


updated = 0

for r in records:
    rid = str(r.get("derrid") or r.get("id") or r.get("report_number") or "")
    if not rid:
        continue

    filename = f"deq_2006_2015_{rid}.html"
    out_path = OUT / filename

    lat = r.get("lat")
    lng = r.get("lng")

    page = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>DEQ Incident {esc(rid)}</title>
  <style>
    body {{ font-family: Georgia, serif; max-width: 850px; margin: 40px auto; line-height: 1.45; }}
    h1 {{ color: #4d6548; }}
    .meta {{ background: #f7f1e8; padding: 16px; border-radius: 10px; }}
    .summary {{ white-space: pre-wrap; margin-top: 20px; }}
  </style>
</head>
<body>
  <h1>Utah DEQ Environmental Incident Record</h1>

  <div class="meta">
    <p><strong>Report #:</strong> {esc(rid)}</p>
    <p><strong>Title:</strong> {esc(r.get("title") or r.get("title_eventname") or r.get("name"))}</p>
    <p><strong>Date:</strong> {esc(r.get("date") or r.get("date_discovered"))}</p>
    <p><strong>County:</strong> {esc(r.get("county"))}</p>
    <p><strong>Company:</strong> {esc(r.get("company") or r.get("responsible_party"))}</p>
    <p><strong>Nearest City:</strong> {esc(r.get("nearest_city") or r.get("city"))}</p>
    {f"<p><strong>Coordinates:</strong> {lat}, {lng}</p>" if lat and lng else ""}
  </div>

  <h2>Incident Summary</h2>
  <div class="summary">{esc(r.get("description") or r.get("incident_summary"))}</div>

  <p><strong>Source:</strong> Utah DEQ Environmental Incident Database archive record.</p>
</body>
</html>
"""

    out_path.write_text(page, encoding="utf-8")
    r["local_source_path"] = str(out_path.relative_to(ROOT)).replace("\\", "/")
    updated += 1

json.dump(records, open(JSON_PATH, "w", encoding="utf-8"), indent=2)

print("Backup:", BACKUP)
print("Source pages created:", updated)
print("Output:", OUT)
