import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime, timedelta
from urllib.parse import urljoin
import os

# --- CONFIG ---
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

# --- HELPER FUNCTIONS ---

def calculate_expiry(posted_date):
    """Expiry = 30 days after posted date"""
    try:
        dt = datetime.strptime(posted_date, "%Y-%m-%d")
    except:
        dt = datetime.utcnow()
    expiry = dt + timedelta(days=30)
    return expiry.strftime("%Y-%m-%d")


def scrape_page(page):
    """Scrape one page of WWR remote jobs"""
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
        title_tag = job.select_one(".title")
        company_tag = job.select_one(".company")
        region_tag = job.select_one(".region")
        if not title_tag:
            continue
        location = (region_tag.text if region_tag else "").lower()
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


# --- SCRAPE MULTIPLE PAGES ---
for page in range(1, 12):  # adjust 1–n pages
    scrape_page(page)
    time.sleep(3)  # polite delay

# --- REMOVE DUPLICATES ---
seen = set()
unique_jobs = []
for job in jobs:
    if job["apply_link"] not in seen:
        unique_jobs.append(job)
        seen.add(job["apply_link"])

# --- REMOVE EXPIRED JOBS ---
today = datetime.utcnow().strftime("%Y-%m-%d")
active_jobs = [job for job in unique_jobs if job["expiry_date"] >= today]

# --- LIMIT TO 200 JOBS ---
active_jobs = active_jobs[:200]

# --- SAVE JOBS ---
with open("jobs.json", "w", encoding="utf-8") as f:
    json.dump(active_jobs, f, indent=2)

print("Jobs scraped:", len(active_jobs))


# --- OPTIONAL: Notify Google for expired jobs ---
# from googleapiclient.discovery import build
# from google.oauth2 import service_account
# GOOGLE_CREDS = os.environ.get("GOOGLE_CREDENTIALS")
# SITE_URL = os.environ.get("SITE_URL", "https://global-job-hub.github.io/jobs/")

# def notify_google(url, action="URL_UPDATED"):
#     """Notify Google Indexing API"""
#     if not GOOGLE_CREDS:
#         return
#     info = json.loads(GOOGLE_CREDS)
#     credentials = service_account.Credentials.from_service_account_info(
#         info, scopes=["https://www.googleapis.com/auth/indexing"]
#     )
#     service = build("indexing", "v3", credentials=credentials)
#     body = {"url": url, "type": action}
#     service.urlNotifications().publish(body=body).execute()
