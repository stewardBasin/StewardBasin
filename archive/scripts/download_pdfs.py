import os
import requests

# =========================
# BASE DIRECTORY
# =========================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

LINK_FILES = [

    os.path.join(BASE_DIR, "county_links.txt"),

    os.path.join(BASE_DIR, "entity_links.txt"),

    os.path.join(BASE_DIR, "complaint_h2s_links.txt"),

    os.path.join(BASE_DIR, "county_links_master.txt"),

    os.path.join(BASE_DIR, "complaint_h2s_links_master.txt"),

]

PDF_FOLDER = os.path.join(BASE_DIR, "pdfs")

os.makedirs(PDF_FOLDER, exist_ok=True)

# =========================
# LOAD LINKS FROM BOTH FILES
# =========================

links = []

for link_file in LINK_FILES:

    if not os.path.exists(link_file):

        print(f"LINK FILE NOT FOUND, SKIPPING: {link_file}")
        continue

    print(f"READING LINKS FROM: {link_file}")

    with open(link_file, "r", encoding="utf-8") as file:

        links.extend(file.readlines())

# =========================
# FILTER PDF LINKS + DEDUPE
# =========================

pdf_links = []

seen = set()

for link in links:

    link = link.strip()

    if not link.startswith("http"):
        continue

    if ".pdf" not in link.lower():
        continue

    if link in seen:
        continue

    seen.add(link)

    pdf_links.append(link)

print(f"\nPDF LINKS FOUND: {len(pdf_links)}")

# =========================
# REQUEST HEADERS
# =========================

headers = {
    "User-Agent": "Mozilla/5.0"
}

# =========================
# DOWNLOAD
# =========================

downloaded = 0
skipped = 0
failed = 0

for url in pdf_links:

    try:

        filename = url.split("/")[-1]
        filename = filename.split("?")[0]

        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"

        save_path = os.path.join(PDF_FOLDER, filename)

        if os.path.exists(save_path):

            print(f"SKIPPING EXISTING: {filename}")
            skipped += 1
            continue

        print("\nDOWNLOADING:")
        print(url)

        response = requests.get(
            url,
            headers=headers,
            timeout=60,
            allow_redirects=True
        )

        if response.status_code != 200:

            print("FAILED STATUS:")
            print(response.status_code)
            failed += 1
            continue

        content_type = response.headers.get("Content-Type", "")

        if "pdf" not in content_type.lower():

            print("NOT PDF CONTENT")
            print(content_type)
            failed += 1
            continue

        if not response.content.startswith(b"%PDF"):

            print("INVALID PDF FILE")
            failed += 1
            continue

        with open(save_path, "wb") as pdf_file:

            pdf_file.write(response.content)

        print("SAVED:")
        print(save_path)

        downloaded += 1

    except Exception as e:

        print("\nFAILED:")
        print(url)
        print(e)

        failed += 1

# =========================
# DONE
# =========================

print("\n====================")
print("DOWNLOAD COMPLETE")
print("====================")
print(f"REAL PDFs SAVED: {downloaded}")
print(f"SKIPPED EXISTING: {skipped}")
print(f"FAILED: {failed}")