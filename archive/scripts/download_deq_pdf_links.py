import os
import requests
from urllib.parse import urlparse, parse_qs

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LINKS_FILE = os.path.join(BASE_DIR, "data", "deq_duchesne_2024_2026_pdf_links.txt")

OUTPUT_DIR = os.path.join(
    BASE_DIR, "raw", "deq_portal_downloads", "duchesne_2024_2026_pdfs"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_record_id(url):
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    return query.get("recordId", ["unknown"])[0]


with open(LINKS_FILE, "r", encoding="utf-8") as f:
    links = [line.strip() for line in f if line.strip()]

print(f"Links found: {len(links)}")

for index, url in enumerate(links, start=1):
    record_id = get_record_id(url)
    filename = f"deq_duchesne_2024_2026_{index:03d}_{record_id}.pdf"
    output_path = os.path.join(OUTPUT_DIR, filename)

    if os.path.exists(output_path):
        print(f"Already exists: {filename}")
        continue

    print(f"Downloading {index}/{len(links)}: {record_id}")

    response = requests.get(url, timeout=60, allow_redirects=True)

    if response.status_code != 200:
        print(f"FAILED {record_id}: HTTP {response.status_code}")
        continue

    with open(output_path, "wb") as f:
        f.write(response.content)

print(f"Done. PDFs saved to: {OUTPUT_DIR}")
print(f"Saving PDFs to: {OUTPUT_DIR}")
