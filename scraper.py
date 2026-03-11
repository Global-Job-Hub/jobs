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
"united states",
"usa",
"united kingdom",
"uk",
"australia",
"canada",
"remote",
"worldwide"
]

jobs = []


def calculate_expiry(posted_date):
    """Expiry = 15 days after posted date"""
    try:
        dt = datetime.strptime(posted_date, "%Y-%m-%d")
    except:
        dt = datetime.utcnow()

    expiry = dt + timedelta(days=15)

    return expiry.strftime("%Y-%m-%d")


def scrape_page(page):

    url = f"{BASE_URL}?page={page}"

    print("Scraping:", url)

    r = requests.get(url, headers=HEADERS, timeout=30)

    soup = BeautifulSoup(r.text, "html.parser")

    listings = soup.select("section.jobs li")

    for job in listings:

        link_tag = job.find("a", href=True)

        if not link_tag:
            continue

        job_url = urljoin(BASE_URL, link_tag["href"])

        title = job.select_one(".title")
        company = job.select_one(".company")
        region = job.select_one(".region")

        if not title:
            continue

        location = (region.text if region else "").lower()

        if not any(x in location for x in TARGET_LOCATIONS):
            continue

        posted_date = datetime.utcnow().strftime("%Y-%m-%d")

        expiry_date = calculate_expiry(posted_date)

        job_data = {
            "id": job_url.split("/")[-1],
            "title": title.text.strip(),
            "company": company.text.strip() if company else "",
            "location": location,
            "apply_link": job_url,
            "source_url": job_url,
            "posted_date": posted_date,
            "expiry_date": expiry_date
        }

        jobs.append(job_data)


# scrape multiple pages
for page in range(1, 12):

    scrape_page(page)

    time.sleep(3)


# remove duplicates
seen = set()
unique_jobs = []

for job in jobs:

    if job["apply_link"] not in seen:

        unique_jobs.append(job)

        seen.add(job["apply_link"])


# remove expired jobs
today = datetime.utcnow().strftime("%Y-%m-%d")

active_jobs = []

for job in unique_jobs:

    if job["expiry_date"] >= today:

        active_jobs.append(job)


# limit to 200 jobs
active_jobs = active_jobs[:200]


with open("jobs.json", "w", encoding="utf-8") as f:

    json.dump(active_jobs, f, indent=2)


print("Jobs scraped:", len(active_jobs))
