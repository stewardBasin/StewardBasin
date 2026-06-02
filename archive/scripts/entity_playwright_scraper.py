import os
import json
import time

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from urllib.parse import urljoin

visited = set()
all_links = set()

# =========================
# CREATE ARCHIVE FOLDERS
# =========================

os.makedirs("archive", exist_ok=True)
os.makedirs("archive/entity_pdfs", exist_ok=True)
os.makedirs("archive/entity_text", exist_ok=True)
os.makedirs("archive/entity_mentions", exist_ok=True)

# =========================
# LOAD ENTITY NAMES
# =========================

ENTITY_FILE = "archive/data/entities.json"

entity_names = []

with open(ENTITY_FILE, "r", encoding="utf-8") as file:

    entities = json.load(file)

    for entity in entities:

        entity_names.append(entity["name"])

# =========================
# START NEW SESSION
# =========================

with open("archive/entity_links.txt", "w", encoding="utf-8") as file:

    file.write("\n========================\n")
    file.write("NEW ENTITY CRAWL SESSION\n")
    file.write("========================\n\n")

# =========================
# START URLS
# =========================

START_URLS = [

    "https://duchesne.utah.gov/gov/dept/cd/",
    "https://duchesne.utah.gov/gov/elected-officials/clerk-auditor/commission-minutes/",
    "https://duchesne.utah.gov/gov/dept/information-systems/gis-maps/",

    "https://www.uintah.utah.gov/",
    "https://www.uintah.utah.gov/departments/community_development/",
    "https://www.uintah.utah.gov/departments/gis_mapping.php",

    "https://www.utetribe.com/",

    "https://oilgas.ogm.utah.gov/",

    "https://documents.deq.utah.gov/",

    "https://le.utah.gov/"

]

# =========================
# SEARCH TERMS
# =========================

SEARCH_TERMS = [

    # LAND USE

    "conditional use permit",
    "CUP",
    "planning commission",
    "public hearing",
    "land use",
    "site plan",
    "variance",
    "zone change",
    "rezone",
    "development agreement",
    "subdivision",
    "master plan",

    # OIL & GAS

    "oil and gas",
    "well pad",
    "compressor station",
    "pipeline",
    "produced water",
    "wastewater",
    "drilling",
    "fracking",
    "hydraulic fracturing",

    # ENVIRONMENT

    "H2S",
    "hydrogen sulfide",
    "benzene",
    "VOC",
    "air quality",
    "odor complaint",
    "spill",
    "contamination",

    # ENFORCEMENT

    "code enforcement",
    "violation",
    "abatement",
    "inspection",
    "incident",
    "lawsuit",

]

# =========================
# ADD ENTITY NAMES
# =========================

SEARCH_TERMS.extend(entity_names)

# =========================
# MAX PAGES
# =========================

MAX_PAGES = 1200

# =========================
# BLOCKED URL PATTERNS
# =========================

BLOCKED_PATTERNS = [

    "googtrans",
    "/translate",
    "?lang=",
    "&lang=",
    "language=",

    "/es/",
    "/fr/",
    "/de/",
    "/ru/",
    "/zh/",
    "/ar/",
    "/ko/",
    "/vi/",

    "facebook.com",
    "twitter.com",
    "linkedin.com",
    "instagram.com",
    "youtube.com",

    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".svg",

    "mailto:",
    "tel:",

]

# =========================
# PRIORITY TERMS
# =========================

PRIORITY_TERMS = [

    "permit",
    "planning",
    "commission",
    "hearing",
    "agenda",
    "minutes",
    "Conditional Use Permit",
    "packet",
    "land-use",
    "development",
    "oil",
    "gas",
    "well",
    "environment",
    "deq",
    "complaint",
    "air",
    "water",
    "waste",
    "h2s",
    "benzene",
    ".pdf"

]

# =========================
# ALLOWED DOMAINS
# =========================

ALLOWED_DOMAINS = [

    "duchesne.utah.gov",
    "uintah.utah.gov",
    "utetribe.com",
    "utah.gov",
    "arcgis.com",
    "tricountyhealth.com",
    "ashleyregional.com",
    "ubmc.org"

]

# =========================
# CRAWLER
# =========================

def crawl(page, url):

    if len(visited) >= MAX_PAGES:
        return

    if url in visited:
        return

    visited.add(url)

    print(f"\nSCANNING: {url}")

    try:

        page.goto(url, timeout=60000)

        page.wait_for_timeout(2500)

        html = page.content()

        soup = BeautifulSoup(html, "html.parser")

        text = soup.get_text().lower()

        # =========================
        # SEARCH TERMS
        # =========================

        for keyword in SEARCH_TERMS:

            if keyword.lower() in text:

                print(f"\nKEYWORD FOUND: {keyword}")
                print(url)

                with open("archive/county_links.txt", "a", encoding="utf-8") as file:

                    file.write(f"KEYWORD: {keyword} | {url}\n")

        # =========================
        # FIND LINKS
        # =========================

        links = soup.find_all("a")

        for link in links:

            href = link.get("href")

            if not href:
                continue

            full_url = urljoin(url, href)

            full_url = full_url.split("#")[0]

            # =========================
            # BLOCK GARBAGE URLS
            # =========================

            if any(pattern in full_url.lower() for pattern in BLOCKED_PATTERNS):
                continue

            # =========================
            # ALLOWED DOMAINS
            # =========================

            if not any(domain in full_url for domain in ALLOWED_DOMAINS):
                continue

            # =========================
            # PRIORITIZE RELEVANT URLS
            # =========================

            if not any(term in full_url.lower() for term in PRIORITY_TERMS):

                continue

            # =========================
            # SAVE LINK
            # =========================

            if full_url not in all_links:

                all_links.add(full_url)

                print(full_url)

                with open("archive/county_links.txt", "a", encoding="utf-8") as file:

                    file.write(full_url + "\n")

            # =========================
            # CONTINUE CRAWL
            # =========================

            if full_url not in visited:

                time.sleep(0.3)

                crawl(page, full_url)

    except Exception as e:

        print(f"\nFAILED: {url}")
        print(e)

        with open("archive/entity_links.txt", "a", encoding="utf-8") as file:

            file.write(f"FAILED: {url}\n")

# =========================
# PLAYWRIGHT
# =========================

with sync_playwright() as p:

    browser = p.chromium.launch(headless=False)

    page = browser.new_page()

    for url in START_URLS:

        crawl(page, url)

    print("\n===================")
    print("TOTAL LINKS FOUND")
    print("===================")

    print(len(all_links))

    print("\nAutosaved to archive/entity_links.txt")

    input("\nPress ENTER to close browser...")

    browser.close()