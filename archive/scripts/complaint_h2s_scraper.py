from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import os

visited = set()
all_links = set()

os.makedirs("archive", exist_ok=True)

OUTPUT_FILE = "archive/complaint_h2s_links.txt"

with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
    file.write("========================\n")
    file.write("STRICT EASTERN UTAH COMPLAINT / REPORT / EXCEEDANCE CRAWL\n")
    file.write("Duchesne County + Uintah County\n")
    file.write("========================\n\n")

START_URLS = [
    "https://documents.deq.utah.gov/",
    "https://airquality.utah.gov/",
    "https://oilgas.ogm.utah.gov/",
    "https://duchesne.utah.gov/gov/dept/cd/",
    "https://duchesne.utah.gov/gov/elected-officials/clerk-auditor/commission-minutes/",
    "https://www.uintah.utah.gov/departments/community_development/",
]

REGION_TERMS = [
    "duchesne",
    "uintah",
    "uinta basin",
    "uintah basin",
    "eastern utah",
    "vernal",
    "roosevelt",
    "fruitland",
    "altamont",
    "myton",
    "ballard",
    "fort duchesne",
]

COMPLAINT_REPORT_TERMS = [
    "complaint",
    "resident complaint",
    "citizen complaint",
    "odor complaint",
    "air complaint",
    "emissions complaint",
    "environmental complaint",
    "complaint investigation",
    "public nuisance",
    "report",
    "incident report",
    "inspection report",
    "monitoring report",
    "annual report",
    "technical report",
    "investigation",
    "inspection",
    "enforcement",
    "notice of violation",
    "violation",
    "noncompliance",
    "compliance order",
    "settlement",
]

AIR_POLLUTION_TERMS = [
    "h2s",
    "hydrogen sulfide",
    "hydrogen sulphide",
    "rotten egg",
    "sulfur odor",
    "sulphur odor",
    "oilfield odor",
    "gas odor",

    "ozone exceedance",
    "ozone nonattainment",
    "ozone standard",
    "8-hour ozone",
    "nonattainment",
    "out of attainment",
    "exceedance",
    "exceeded",
    "above standard",
    "above the standard",

    "pm2.5",
    "pm 2.5",
    "pm10",
    "pm 10",
    "particulate matter",
    "fugitive dust",
    "dust complaint",

    "benzene exceedance",
    "benzene violation",
    "benzene complaint",
    "benzene monitoring",
    "volatile organic compounds exceedance",
    "volatile organic compounds violation",
    "volatile organic compounds complaint",
    "voc exceedance",
    "voc violation",
    "voc complaint",
    "voc monitoring",
    "voc report",
]

WATER_SPILL_TERMS = [
    "spill",
    "release",
    "unauthorized discharge",
    "unauthorized release",
    "water contamination",
    "groundwater contamination",
    "surface water contamination",
    "produced water spill",
    "produced water release",
    "wastewater incident",
    "pipeline leak",
    "leak investigation",
    "cleanup",
]

URL_PRIORITY_TERMS = [
    "complaint",
    "investigation",
    "report",
    "monitoring",
    "inspection",
    "violation",
    "enforcement",
    "noncompliance",
    "compliance",
    "exceedance",
    "nonattainment",
    "h2s",
    "hydrogen",
    "sulfide",
    "ozone",
    "pm2",
    "pm10",
    "particulate",
    "dust",
    "spill",
    "release",
    "discharge",
    "contamination",
    "benzene",
    "air-quality",
    "airquality",
    "water-quality",
    "duchesne",
    "uintah",
    "uinta",
    "basin",
]

ALLOWED_DOMAINS = [
    "documents.deq.utah.gov",
    "airquality.utah.gov",
    "oilgas.ogm.utah.gov",
    "duchesne.utah.gov",
    "uintah.utah.gov",
]

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
    "schools.utah.gov",
    "student",
    "teacher",
    "classroom",
    "facebook.com",
    "twitter.com",
    "linkedin.com",
    "instagram.com",
    "youtube.com",
    "google.com/calendar",
    "outlook",
    "webcal",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".svg",
    "mailto:",
    "tel:",
    "tribe_events",
    "tribe-bar-date",
    "eventdisplay",
    "eventdate",
    "/events/",
    "/event/",
    "/calendar/",
    "ical",
    "/month/",
    "/today/",
    "/summary/",
    "/day/",
    "paged=",
    "page/2",
]

MAX_PAGES = 600
MAX_URL_LENGTH = 220


def save_line(line):
    with open(OUTPUT_FILE, "a", encoding="utf-8") as file:
        file.write(line + "\n")


def contains_any(text, terms):
    lower = text.lower()
    return any(term in lower for term in terms)


def has_region(text):
    return contains_any(text, REGION_TERMS)


def has_real_issue(text):
    lower = text.lower()

    complaint_or_report = contains_any(lower, COMPLAINT_REPORT_TERMS)
    air_issue = contains_any(lower, AIR_POLLUTION_TERMS)
    water_spill = contains_any(lower, WATER_SPILL_TERMS)

    return (
        complaint_or_report and (air_issue or water_spill)
    ) or (
        air_issue and contains_any(
            lower,
            [
                "exceedance",
                "exceeded",
                "above standard",
                "above the standard",
                "violation",
                "noncompliance",
                "enforcement",
                "monitoring report",
                "inspection report",
            ],
        )
    ) or water_spill


def has_priority_url(url):
    lower = url.lower()

    # Do not let bare VOC pull the crawl forward.
    if "voc" in lower and not any(
        term in lower
        for term in [
            "exceedance",
            "violation",
            "complaint",
            "monitoring",
            "report",
            "enforcement",
            "noncompliance",
        ]
    ):
        return False

    return any(term in lower for term in URL_PRIORITY_TERMS)


def allowed_url(url):
    lower = url.lower()

    if len(url) > MAX_URL_LENGTH:
        return False

    if any(pattern in lower for pattern in BLOCKED_PATTERNS):
        return False

    if not any(domain in lower for domain in ALLOWED_DOMAINS):
        return False

    return True


def crawl(page, url):

    if len(visited) >= MAX_PAGES:
        return

    if url in visited:
        return

    if not allowed_url(url):
        return

    visited.add(url)

    print(f"\nSCANNING: {url}")
    save_line(f"SCANNED: {url}")

    try:
        page.goto(url, timeout=60000)
        page.wait_for_timeout(2000)

        html = page.content()
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(" ", strip=True)
        lower_text = text.lower()

        region_match = has_region(lower_text)
        issue_match = has_real_issue(lower_text)

        if region_match and issue_match:
            print("\nRELEVANT PAGE FOUND:")
            print(url)
            save_line(f"RELEVANT: {url}")

            for keyword in (
                COMPLAINT_REPORT_TERMS
                + AIR_POLLUTION_TERMS
                + WATER_SPILL_TERMS
            ):
                if keyword in lower_text:
                    print(f"KEYWORD FOUND: {keyword}")
                    save_line(f"KEYWORD: {keyword} | {url}")

        links = soup.find_all("a")

        for link in links:
            href = link.get("href")

            if not href:
                continue

            full_url = urljoin(url, href)
            full_url = full_url.split("#")[0]

            if not allowed_url(full_url):
                continue

            is_pdf = ".pdf" in full_url.lower()

            if not is_pdf and not has_priority_url(full_url):
                continue

            if is_pdf and not has_priority_url(full_url):
                # PDFs with generic names are skipped unless URL has evidence terms.
                continue

            if full_url not in all_links:
                all_links.add(full_url)
                print(full_url)
                save_line(full_url)

            if full_url not in visited:
                time.sleep(0.3)
                crawl(page, full_url)

    except Exception as e:
        print(f"\nFAILED: {url}")
        print(e)
        save_line(f"FAILED: {url}")


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    for url in START_URLS:
        crawl(page, url)

    print("\n===================")
    print("TOTAL LINKS FOUND")
    print("===================")
    print(len(all_links))

    print(f"\nAutosaved to {OUTPUT_FILE}")

    input("\nPress ENTER to close browser...")

    browser.close()