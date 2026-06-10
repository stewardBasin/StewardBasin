import os
import re
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

URL = "https://deqspillsps.deq.utah.gov/s/"
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "deq_uintah_2024_2026_pdf_links.txt")
DEBUG_HTML = os.path.join(BASE_DIR, "data", "debug_deq_uintah_2024_2026_page.html")

EXPECTED_COUNT = 41


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto(URL, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(8000)

        print("In the browser:")
        print("1. Set Date From = Jan 1, 2024")
        print("2. Set Date To = today")
        print("3. Set County = UINTAH")
        print("4. Click Search")
        print("5. Confirm it says 41 spills found")
        input("Then press ENTER here...")

        # Save the rendered page for debugging.
        html = page.content()
        with open(DEBUG_HTML, "w", encoding="utf-8") as f:
            f.write(html)

        # Extract Salesforce record IDs from the rendered page/source.
        record_ids = set(re.findall(r"500[a-zA-Z0-9]{12,18}", html))

        # Also search visible page text, just in case IDs render there.
        text = page.locator("body").inner_text()
        record_ids.update(re.findall(r"500[a-zA-Z0-9]{12,18}", text))

        links = sorted(
            f"https://deqspillsps.deq.utah.gov/s/pdfdownload?recordId={rid}"
            for rid in record_ids
        )

        print(f"Record IDs found: {len(record_ids)}")

        if len(links) != EXPECTED_COUNT:
            print(f"STOP: expected {EXPECTED_COUNT} links, found {len(links)}.")
            print(f"Debug HTML saved: {DEBUG_HTML}")
            browser.close()
            return

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            for link in links:
                f.write(link + "\n")

        print("Saved:", OUTPUT_FILE)
        browser.close()


if __name__ == "__main__":
    main()
