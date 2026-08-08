import os
import re
import requests
from bs4 import BeautifulSoup

from fake_useragent import UserAgent
import requests

from debug_print import debug_print

# Setup
session = None

def change_session():
    global session
    
    debug_print("Changing session", 3)

    ua = UserAgent()
    headers = {
        "User-Agent": ua.random,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1"
    }

    session = requests.Session()
    session.headers.update(headers) # Global fallback browser footprint

    debug_print("  └── Session changed.", 3)

def extract_pdf_download_links(year):
    global session
    BASE_DOMAIN = "https://laws.gov.tt"
    TARGET_URL = f"https://laws.gov.tt/ttdll-web/revision/bylegalnotice?year={year}"

    debug_print(f"Extracting {year} pdf download links", 1)
    response = session.get(TARGET_URL)
    soup = BeautifulSoup(response.text, "html.parser")

    # Find all table rows
    rows = soup.find_all("tr")
    pdf_download_links = []

    i = 0
    for i in range(len(rows)):
        row = rows[i]
        row_text = row.get_text()
        
        # Filter only rows containing "DETENTION ORDER"
        if "DETENTION ORDER" in row_text.upper():
            # Find the download link anchor tag
            link_tag = row.find("a", href=re.compile(r"/download/"))

            if link_tag and link_tag.get("href"):
                relative_url = link_tag["href"]
                download_url = f"{BASE_DOMAIN}{relative_url}" if relative_url.startswith("/") else relative_url
                
                # Extract Legal Notice Number for file naming (e.g., "LN. 539/2026" -> "LN_539_2026")
                ln_tag = row.find("strong")
                if ln_tag:
                    clean_ln = re.sub(r"[^\w\-]", "_", ln_tag.get_text().replace(".", "").strip())
                    id = f"{clean_ln}.pdf"
                else:
                    id = f"detention_order_{i + 1}.pdf"

                pdf_download_links.append((id, download_url))

    debug_print("  └── PDF download links extracted.", 1)
    return pdf_download_links

def download_pdf_temp(id, link):
    global session

    debug_print(f"Downloading {id} temporarily", 1)
    filepath = os.path.join("./detention_order_temp.pdf")
    pdf_res = session.get(link)
    
    if pdf_res.status_code == 200:
        with open(filepath, "wb") as f:
            f.write(pdf_res.content)

        debug_print("  └── PDF downloaded.", 1)
    else:
        debug_print(f"  └── Failed to download (HTTP {pdf_res.status_code}).", 1)
        debug_print(f"  └── Response:\n{BeautifulSoup(pdf_res.text, 'html.parser')}.", 1)

