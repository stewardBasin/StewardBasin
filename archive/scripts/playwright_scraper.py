from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import os

visited = set()
all_links = set()

os.makedirs("archive", exist_ok=True)

with open("archive/county_links.txt", "a", encoding="utf-8") as file:
    file.write("\n\n========================\n")
    file.write("NEW COUNTY CRAWL SESSION\n")
    file.write("========================\n")

START_URLS = [
    "https://duchesne.utah.gov/gov/dept/cd/",
    "https://duchesne.utah.gov/gov/elected-officials/clerk-auditor/commission-minutes/",
    "https://duchesne.utah.gov/gov/dept/information-systems/gis-maps/",

    "https://www.uintah.utah.gov/",
    "https://www.uintah.utah.gov/departments/community_development/",
    "https://www.uintah.utah.gov/departments/gis_mapping.php",

    "https://www.utetribe.com/",
    "https://www.utetribe.com/departments",

    "https://oilgas.ogm.utah.gov/oilgasweb/live-data-search/lds-map/lds-map.xhtml",

    "https://tricountyhealth.com/",
    "https://ashleyregional.com/",
    "https://ubmc.org/",
    "https://healthdata.gov/",
    "https://dhhs.utah.gov/",
    "https://ibis.utah.gov/",
    "https://epi.utah.gov/",
]

SEARCH_TERMS = [
    "cancer", "COPD", "asthma", "respiratory illness", "lung disease",
    "birth defects", "miscarriage", "maternal mortality", "infant mortality",
    "hospitalization", "emergency room", "ER visits", "heart disease",
    "stroke", "mortality", "morbidity", "tribal health", "mental health",
    "suicide", "opioid", "methamphetamine",

    "odor", "smell", "fumes", "air quality", "air pollution", "dust",
    "silica", "PM2.5", "PM10", "smoke", "emissions", "pollution",
    "contamination", "spill", "oil spill", "cleanup", "groundwater",
    "water contamination", "pipeline leak", "flare", "flaring", "H2S",
    "hydrogen sulfide", "benzene", "VOC",

    "noise", "traffic", "truck traffic", "road damage", "light pollution",
    "public nuisance", "quality of life", "complaint", "resident complaint",

    "oil and gas", "well pad", "drilling", "fracking",
    "hydraulic fracturing", "compressor station", "processing plant",
    "industrial facility", "mine", "pipeline", "refinery",

    "conditional use permit", "CUP", "public hearing", "planning commission",
    "zone change", "rezone", "land use", "variance", "resident opposition",
    "citizen comments",

    "Ute", "Ute Tribe", "Uintah and Ouray", "tribal", "reservation",
    "Indian Country", "MMIW", "missing and murdered indigenous women",
    "violence against women", "domestic violence", "sexual assault", "rape",
    "human trafficking", "protective order", "abuse", "harassment",
    "man camp", "employee housing", "oil field housing",

    "code enforcement", "violation", "lawsuit", "litigation", "citation",
    "abatement", "inspection", "incident",

    "Ovintiv", "XCL Resources", "Crescent Point", "Crescent Point Energy",
    "Anschutz", "JR Bird", "Christine Watkins", "Ron Winterton",
    "Nine Mile LLC", "Energence LLC", "Vaibhav Shree LLC", "Javelin",
    "Jacob Woodland", "Jake Woodland", "Mike Stegnal", "Michael Stegnal",
    "reWater LLC", "Wasatch Energy", "KGH Operating Company",
]

MAX_PAGES = 1200

BLOCKED_PATTERNS = [
    "googtrans", "/translate", "?lang=", "&lang=", "language=",
    "/es/", "/fr/", "/de/", "/ru/", "/zh/", "/ar/", "/ko/", "/vi/",
    "schools.utah.gov", "student", "teacher", "classroom",
    "facebook.com", "twitter.com", "linkedin.com", "instagram.com", "youtube.com",
    ".jpg", ".jpeg", ".png", ".gif", ".svg",
    "mailto:", "tel:",
]

ALLOWED_DOMAINS = [
    "duchesne.utah.gov",
    "uintah.utah.gov",
    "utetribe.com",
    "oilgas.ogm.utah.gov",
    "tricountyhealth.com",
    "ashleyregional.com",
    "ubmc.org",
    "healthdata.gov",
    "dhhs.utah.gov",
    "ibis.utah.gov",
    "epi.utah.gov",
    "arcgis.com",
]

def crawl(page, url):
    if len(visited) >= MAX_PAGES:
        return

    if url in visited:
        return

    visited.add(url)

    print(f"\nSCANNING: {url}")

    with open("archive/county_links.txt", "a", encoding="utf-8") as file:
        file.write(f"SCANNED: {url}\n")

    try:
        page.goto(url, timeout=60000)
        page.wait_for_timeout(2000)

        html = page.content()
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text().lower()

        for keyword in SEARCH_TERMS:
            if keyword.lower() in text:
                print(f"\nKEYWORD FOUND: {keyword}")
                print(url)

                with open("archive/county_links.txt", "a", encoding="utf-8") as file:
                    file.write(f"KEYWORD: {keyword} | {url}\n")

        links = soup.find_all("a")

        for link in links:
            href = link.get("href")

            if not href:
                continue

            full_url = urljoin(url, href)
            full_url = full_url.split("#")[0]

            if any(pattern in full_url.lower() for pattern in BLOCKED_PATTERNS):
                continue

            if not any(domain in full_url for domain in ALLOWED_DOMAINS):
                continue

            if full_url not in all_links:
                all_links.add(full_url)
                print(full_url)

                with open("archive/county_links.txt", "a", encoding="utf-8") as file:
                    file.write(full_url + "\n")

            if full_url not in visited:
                time.sleep(0.3)
                crawl(page, full_url)

    except Exception as e:
        print(f"\nFAILED: {url}")
        print(e)

        with open("archive/county_links.txt", "a", encoding="utf-8") as file:
            file.write(f"FAILED: {url}\n")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    for url in START_URLS:
        crawl(page, url)

    print("\n===================")
    print("TOTAL LINKS FOUND")
    print("===================")
    print(len(all_links))

    print("\nAutosaved to archive/county_links.txt")

    input("\nPress ENTER to close browser...")

    browser.close()