from pathlib import Path
from urllib.parse import urlparse, parse_qs
import requests

BASE_DIR = Path(__file__).resolve().parents[1]

LINKS_FILE = BASE_DIR / "data" / "deq_duchesne_2024_2026_pdf_links.txt"
OUTPUT_DIR = BASE_DIR / "pdfs" / "deq_duchesne_2024_2026_real"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_record_id(url):
    return parse_qs(urlparse(url).query).get("recordId", ["unknown"])[0]


def main():
    links = [
        line.strip()
        for line in LINKS_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    print(f"Found {len(links)} links")

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/pdf,text/html,*/*",
        }
    )

    for index, old_url in enumerate(links, start=1):
        record_id = get_record_id(old_url)
        pdf_url = f"https://deqspillsps.deq.utah.gov/apex/CaseToPDF?id={record_id}"
        output_path = OUTPUT_DIR / f"deq_duchesne_2024_2026_{index:03d}_{record_id}.pdf"

        if output_path.exists():
            print(f"Already exists {index}/{len(links)}: {output_path.name}")
            continue

        print(f"Downloading {index}/{len(links)}: {record_id}")

        response = session.get(pdf_url, timeout=60)

        content_type = response.headers.get("content-type", "")
        if response.status_code != 200 or "pdf" not in content_type.lower():
            print(f"FAILED {record_id}: {response.status_code} {content_type}")
            continue

        output_path.write_bytes(response.content)
        print(f"Saved: {output_path.name}")

    print("Done.")


if __name__ == "__main__":
    main()
