import json
import os
import shutil
import time
from datetime import datetime
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from pyproj import Transformer

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_FILE = os.path.join(BASE_DIR, "data", "deq_uintah_2020_2024.json")
SEARCH_URL = "https://eqspillsps.deq.utah.gov/Search_Public.aspx"

SEARCH_DATE = "01/01/2020"
COUNTY_LABEL = "UINTAH"

TRANSFORMER = Transformer.from_crs("EPSG:26912", "EPSG:4326", always_xy=True)


def load_records():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_records(records):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)


def backup_file():
    backup = os.path.join(
        BASE_DIR,
        "data",
        f"deq_uintah_2020_2024_before_coords_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
    )
    shutil.copyfile(DATA_FILE, backup)
    return backup


def utm_to_lat_lng(utme, utmn):
    lng, lat = TRANSFORMER.transform(float(utme), float(utmn))
    return lat, lng


def get_utm_from_url(url):
    qs = parse_qs(urlparse(url).query)
    return qs.get("UTMn", [None])[0], qs.get("UTMe", [None])[0]


def close_disclaimer(page):
    try:
        page.click('input[value="OK"]', timeout=5000)
        print("Closed disclaimer.")
    except Exception:
        print("No disclaimer popup.")


def set_date_filter_after_2020(page):
    page.wait_for_selector(
        "#ctl00_ContentPlaceHolder1_txtIncident_start_date",
        timeout=30000,
    )

    page.evaluate(
        """
        ({ dateValue }) => {
            const dateBox = document.querySelector("#ctl00_ContentPlaceHolder1_txtIncident_start_date");
            if (!dateBox) {
                throw new Error("Date box not found");
            }

            dateBox.removeAttribute("readonly");
            dateBox.value = dateValue;
            dateBox.dispatchEvent(new Event("input", { bubbles: true }));
            dateBox.dispatchEvent(new Event("change", { bubbles: true }));

            const row = dateBox.closest("tr");
            if (!row) {
                throw new Error("Date row not found");
            }

            const radios = Array.from(row.querySelectorAll("input[type='radio']"));
            if (radios.length < 3) {
                throw new Error("Expected at least 3 date operator radios, found " + radios.length);
            }

            const greaterThanRadio = radios[2];

            greaterThanRadio.checked = true;
            greaterThanRadio.click();
            greaterThanRadio.dispatchEvent(new Event("change", { bubbles: true }));
        }
        """,
        {"dateValue": SEARCH_DATE},
    )


def main():
    records = load_records()
    backup = backup_file()

    print(f"Loaded records: {len(records)}")
    print(f"Backup saved: {backup}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        print("Opening DEQ page...")
        page.goto(SEARCH_URL, wait_until="networkidle", timeout=60000)

        close_disclaimer(page)
        page.wait_for_load_state("networkidle", timeout=60000)
        page.wait_for_timeout(1000)

        print("Setting date filter: Date Discovered > 01/01/2020")
        set_date_filter_after_2020(page)

        print("Selecting Duchesne County...")
        page.select_option(
            'select[name="ctl00$ContentPlaceHolder1$ddlCounty"]',
            label=COUNTY_LABEL,
        )

        print("Running search...")
        page.click("#ctl00_ContentPlaceHolder1_cmdSearch")
        page.wait_for_load_state("networkidle", timeout=60000)
        page.wait_for_timeout(2000)

        debug_png = os.path.join(BASE_DIR, "data", "debug_deq_map_search.png")
        page.screenshot(path=debug_png, full_page=True)
        print(f"Debug screenshot saved: {debug_png}")

        map_links = page.locator('a[id*="cmdViewMap"]')
        total_maps = map_links.count()

        print(f"Map links found: {total_maps}")
        print(f"JSON records found: {len(records)}")

        map_urls = []

        for i in range(total_maps):
            print(f"Opening map {i + 1}/{total_maps}...")

            try:
                with page.expect_popup(timeout=15000) as popup_info:
                    map_links.nth(i).click()

                popup = popup_info.value
                popup.wait_for_load_state("domcontentloaded", timeout=15000)
                map_url = popup.url
                popup.close()

                print(f"  {map_url}")
                map_urls.append(map_url)

            except PlaywrightTimeoutError:
                print("  Popup timeout.")
                map_urls.append(None)

            except Exception as e:
                print(f"  Failed: {e}")
                map_urls.append(None)

            time.sleep(0.15)

        browser.close()

    good_urls = [u for u in map_urls if u and "UTMn=" in u and "UTMe=" in u]

    print(f"Good map URLs with UTM: {len(good_urls)}")

    limit = min(len(good_urls), len(records))

    for i in range(limit):
        record = records[i]
        map_url = good_urls[i]

        utmn, utme = get_utm_from_url(map_url)

        if not utmn or not utme:
            record["map_url"] = map_url
            record["review_status"] = "map_url_missing_utm"
            continue

        lat, lng = utm_to_lat_lng(utme, utmn)

        record["utm_northing"] = utmn
        record["utm_easting"] = utme
        record["lat"] = lat
        record["lng"] = lng
        record["the_geom"] = {
            "type": "Point",
            "coordinates": [lng, lat],
        }
        record["map_url"] = map_url
        record["location_confidence"] = "deq_map_link_utm_converted"
        record["map_ready"] = True
        record["review_status"] = "mapped_from_deq_map_link"

    save_records(records)

    mapped = [
        r for r in records if r.get("the_geom") and r["the_geom"].get("coordinates")
    ]

    print()
    print("===================================")
    print("DEQ UINTAH COORDS DONE")
    print("===================================")
    print(f"Records: {len(records)}")
    print(f"Mapped: {len(mapped)}")
    print(f"Saved: {DATA_FILE}")


if __name__ == "__main__":
    main()
