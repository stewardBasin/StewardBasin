from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
import time

OUT_FILE = "archive/uintah_public_record_links.txt"

START_URLS = [
    "https://www.uintah.utah.gov/",
    "https://www.uintah.utah.gov/departments/community_development/",
    "https://www.uintah.utah.gov/departments/gis_mapping.php",
]

SEARCH_TERMS = [
    "planning commission",
    "county commission",
    "minutes",
    "agenda",
    "public hearing",
    "public comment",
    "citizen comments",
    "conditional use permit",
    "CUP",
    "land use",
    "zone change",
    "oil and gas",
    "drilling",
    "well pad",
    "compressor station",
    "dust",
    "odor",
    "smell",
    "noise",
    "truck traffic",
    "flare",
    "flaring",
    "H2S",
    "hydrogen sulfide",
    "resident complaint",
    "raised concerns",
    "opposition",
]

BLOCKED = [
    "facebook",
    "twitter",
    "instagram",
    "youtube",
    "mailto:",
    "tel:",
    ".jpg",
    ".png",
    ".gif",
    ".svg",
]

visited = set()
found_links = set()

os.makedirs("archive", exist_ok=True)

with open(OUT_FILE, "w", encoding="utf-8") as f:
    f.write("UINTAH PUBLIC RECORD CRAWL\n\n")


def allowed(url):
    lower = url.lower()

    if any(b in lower for b in BLOCKED):
        return False

    return "uintah.utah.gov" in lower


def crawl(page, url, depth=0):
    if depth > 4:
        return

    if url in visited:
        return

    visited.add(url)

    print("SCANNING:", url)

    try:
        page.goto(url, timeout=60000)
        page.wait_for_timeout(1500)

        html = page.content()
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(" ", strip=True).lower()

        matched = [term for term in SEARCH_TERMS if term.lower() in text]

        if matched:
            with open(OUT_FILE, "a", encoding="utf-8") as f:
                f.write(f"\nSCANNED: {url}\n")
                for term in matched:
                    f.write(f"KEYWORD: {term} | {url}\n")

        for a in soup.find_all("a"):
            href = a.get("href")
            if not href:
                continue

            full = urljoin(url, href).split("#")[0]

            if not allowed(full):
                continue

            if full not in found_links:
                found_links.add(full)

                with open(OUT_FILE, "a", encoding="utf-8") as f:
                    f.write(full + "\n")

            crawl(page, full, depth + 1)
            time.sleep(0.2)

    except Exception as e:
        print("FAILED:", url, e)


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    for url in START_URLS:
        crawl(page, url)

    browser.close()

print("Done.")
print("Visited:", len(visited))
print("Links found:", len(found_links))
print("Saved:", OUT_FILE)
