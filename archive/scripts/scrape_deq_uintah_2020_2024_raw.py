import os
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SEARCH_URL = "https://eqspillsps.deq.utah.gov/Search_Public.aspx"
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "deq_uintah_2020_2024_raw.txt")

SEARCH_DATE = "01/01/2020"
COUNTY_LABEL = "UINTAH"


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
            if (!dateBox) throw new Error("Date box not found");

            dateBox.removeAttribute("readonly");
            dateBox.value = dateValue;
            dateBox.dispatchEvent(new Event("input", { bubbles: true }));
            dateBox.dispatchEvent(new Event("change", { bubbles: true }));

            const row = dateBox.closest("tr");
            const radios = Array.from(row.querySelectorAll("input[type='radio']"));
            if (radios.length < 3) {
                throw new Error("Expected at least 3 date operator radios");
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
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        print("Opening DEQ legacy search...")
        page.goto(SEARCH_URL, wait_until="networkidle", timeout=60000)

        close_disclaimer(page)
        page.wait_for_timeout(1000)

        print("Setting date filter: Date Discovered > 01/01/2020")
        set_date_filter_after_2020(page)

        print("Selecting Uintah County...")
        page.select_option(
            'select[name="ctl00$ContentPlaceHolder1$ddlCounty"]',
            label=COUNTY_LABEL,
        )

        print("Running search...")
        page.click("#ctl00_ContentPlaceHolder1_cmdSearch")
        page.wait_for_load_state("networkidle", timeout=60000)
        page.wait_for_timeout(2000)

        text = page.locator("body").inner_text()

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(text)

        print("Saved raw text:", OUTPUT_FILE)
        print("Raw text length:", len(text))

        browser.close()


if __name__ == "__main__":
    main()
