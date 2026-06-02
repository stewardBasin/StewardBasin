import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

URLS = [
    "https://duchesne.utah.gov",
    "https://duchesne.utah.gov/commission/",
    "https://duchesne.utah.gov/community-development/",
    "https://duchesne.utah.gov/planning-zoning/",
]

headers = {
    "User-Agent": "Mozilla/5.0"
}

all_pdfs = []

for url in URLS:

    print(f"\nSCANNING: {url}")

    try:
        response = requests.get(url, headers=headers)

        soup = BeautifulSoup(response.text, "html.parser")

        for link in soup.find_all("a", href=True):

            href = link["href"]

            if ".pdf" in href.lower():

                full_url = urljoin(url, href)

                if full_url not in all_pdfs:
                    all_pdfs.append(full_url)

    except Exception as e:
        print("ERROR:", e)

print("\n========================")
print("FOUND PDF FILES")
print("========================\n")

for pdf in all_pdfs:
    print(pdf)