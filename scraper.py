import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime, timedelta
from urllib.parse import urljoin

BASE_URL = "https://weworkremotely.com/remote-jobs"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

TARGET_LOCATIONS = [
    "united states", "usa", "united kingdom", "uk", 
    "australia", "canada", "remote", "worldwide"
]

jobs = []

def calculate_expiry(posted_date):
    dt = datetime.strptime(posted_date, "%Y-%m-%d")
    expiry = dt + timedelta(days=30)
    return expiry.strftime("%Y-%m-%d")

def scrape_page(page):
    url = f"{BASE_URL}?page={page}"
    print("Scraping:", url)
    r = requests.get(url, headers=HEADERS, timeout=30)
    soup = BeautifulSoup(r.text, "html.parser")

    # Each section.jobs contains <li> elements
    listings = soup.select("section.jobs ul li")

    for li in listings:
        # Skip dividers / empty li
        if 'class' in li.attrs and 'view-all' in li.attrs['class']:
            continue

        link_tag = li.find("a", href=True)
        if not link_tag:
            continue

        job_url = urljoin(BASE_URL, link_tag["href"])
        company_tag = li.select_one(".company")
        title_tag = li.select_one(".title")
        region_tag = li.select_one(".region")

        if not title_tag:
            continue

        location = (region_tag.text.strip() if region_tag else "").lower()
        if not any(x in location for x in TARGET_LOCATIONS):
            continue

        posted_date = datetime.utcnow().strftime("%Y-%m-%d")
        expiry_date = calculate_expiry(posted_date)

        jobs.append({
            "id": job_url.split("/")[-1],
            "title": title_tag.text.strip(),
            "company": company_tag.text.strip() if company_tag else "",
            "location": location,
            "apply_link": job_url,
            "source_url": job_url,
            "posted_date": posted_date,
            "expiry_date": expiry_date
        })

for page in range(1, 12):
    scrape_page(page)
    time.sleep(2)  # polite delay

# Deduplicate
seen = set()
unique_jobs = []
for job in jobs:
    if job["apply_link"] not in seen:
        unique_jobs.append(job)
        seen.add(job["apply_link"])

# Remove expired jobs
today = datetime.utcnow().strftime("%Y-%m-%d")
active_jobs = [job for job in unique_jobs if job["expiry_date"] >= today]

# Limit 200
active_jobs = active_jobs[:200]

# Save
with open("jobs.json", "w", encoding="utf-8") as f:
    json.dump(active_jobs, f, indent=2)

print("Jobs scraped:", len(active_jobs))
