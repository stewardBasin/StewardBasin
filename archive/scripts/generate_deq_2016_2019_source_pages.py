import html
import json
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JSON_PATH = ROOT / "archive" / "data" / "deq_environmental_incidents_basin.json"
OUT_DIR = ROOT / "archive" / "sources" / "deq_2016_2019_records"

BACKUP = JSON_PATH.with_name(
    f"deq_environmental_incidents_basin_before_2016_2019_source_pages_{datetime.now():%Y%m%d_%H%M%S}.json"
)


def esc(value):
    if value is None or value == "":
        return "Unknown"
    return html.escape(str(value))


def get_year(record):
    for key in [
        "date_discovered_for_filter",
        "date_discovered_iso",
        "date_discovered",
        "date",
    ]:
        val = str(record.get(key) or "")
        if val.startswith(("2016", "2017", "2018", "2019")):
            return val[:4]
        for year in ["2016", "2017", "2018", "2019"]:
            if f"/{year}" in val or year in val:
                return year
    return ""


def coords(record):
    if record.get("latitude") and record.get("longitude"):
        return f'{record.get("latitude")}, {record.get("longitude")}'
    if record.get("the_geom", {}).get("coordinates"):
        lng, lat = record["the_geom"]["coordinates"]
        return f"{lat}, {lng}"
    return "Unknown"


def make_filename(record):
    rid = (
        record.get("derrid") or record.get("id") or record.get("objectid") or "unknown"
    )
    return f"deq_2016_2019_{rid}.html"


shutil.copyfile(JSON_PATH, BACKUP)
OUT_DIR.mkdir(parents=True, exist_ok=True)

records = json.load(open(JSON_PATH, encoding="utf-8"))

created = 0

for r in records:
    year = get_year(r)
    if year not in {"2016", "2017", "2018", "2019"}:
        continue

    filename = make_filename(r)
    rel_path = f"archive/sources/deq_2016_2019_records/{filename}"
    out_path = OUT_DIR / filename

    title = (
        r.get("title_eventname")
        or r.get("name")
        or r.get("title")
        or "DEQ Environmental Incident"
    )

    report_id = r.get("derrid") or r.get("id") or r.get("objectid")
    date = r.get("date_discovered") or r.get("date_discovered_iso") or r.get("date")
    county = r.get("county")
    company = r.get("responsible_party") or r.get("company")
    nearest_city = r.get("nearest_city") or r.get("city")
    summary = r.get("incident_summary") or r.get("description") or ""

    source_url = ""
    if r.get("source_url") and report_id:
        source_url = f'{r.get("source_url")}?id={report_id}'

    html_text = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>DEQ Incident {esc(report_id)}</title>
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
    <p><strong>Report #:</strong> {esc(report_id)}</p>
    <p><strong>Title:</strong> {esc(title)}</p>
    <p><strong>Date:</strong> {esc(date)}</p>
    <p><strong>County:</strong> {esc(county)}</p>
    <p><strong>Company:</strong> {esc(company)}</p>
    <p><strong>Nearest City:</strong> {esc(nearest_city)}</p>
    <p><strong>Coordinates:</strong> {esc(coords(r))}</p>
  </div>

  <h2>Incident Summary</h2>
  <div class="summary">{esc(summary)}</div>

  <h2>Source Information</h2>

<p><strong>Steward Basin Archive:</strong> This page is a locally archived copy of a Utah DEQ Environmental Incident open-data record preserved by Steward Basin.</p>

{f'<p><strong>Original Source:</strong> <a href="{esc(source_url)}" target="_blank" rel="noopener">Utah DEQ Open Data Environmental Incident Record</a></p>' if source_url else ''}
</body>
</html>
"""

    out_path.write_text(html_text, encoding="utf-8")
    r["local_source_path"] = rel_path
    r["source_url_status"] = "local_archive_from_deq_open_data"
    created += 1

json.dump(records, open(JSON_PATH, "w", encoding="utf-8"), indent=2)

print("Backup:", BACKUP)
print("2016-2019 source pages created:", created)
print("Output:", OUT_DIR)
