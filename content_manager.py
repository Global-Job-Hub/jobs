import os
import sys
import json
import re
import datetime
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- CONFIG ---
SITE_URL = os.environ.get("SITE_URL", "https://global-job-hub.github.io/jobs/")
JOOBLE_KEY = os.environ.get("JOOBLE_API_KEY")
GOOGLE_CREDS = os.environ.get("GOOGLE_CREDENTIALS")

# Ads Configuration
ADS = {
    "AD_728X90": os.environ.get("AD_728X90", ""),
    "AD_300X250": os.environ.get("AD_300X250", ""),
    "AD_468X60": os.environ.get("AD_468X60", ""),
    "AD_160X600": os.environ.get("AD_160X600", ""),
    "AD_160X300": os.environ.get("AD_160X300", ""),
    "AD_320X50": os.environ.get("AD_320X50", ""),
    "AD_NATIVE": os.environ.get("AD_NATIVE", "")
}

def notify_google(url):
    """Sends a notification to Google Indexing API."""
    if not GOOGLE_CREDS:
        print(f"⚠️ Google Indexing skipped: Credentials not found for {url}")
        return
    try:
        info = json.loads(GOOGLE_CREDS)
        credentials = service_account.Credentials.from_service_account_info(
            info, scopes=["https://www.googleapis.com/auth/indexing"]
        )
        service = build("indexing", "v3", credentials=credentials)
        body = {"url": url, "type": "URL_UPDATED"}
        service.urlNotifications().publish(body=body).execute()
        print(f"🚀 Google Notified: {url}")
    except Exception as e:
        print(f"❌ Google Indexing Error: {e}")

def fetch_jobs():
    """Fetches jobs from Jooble and logs quota."""
    if not JOOBLE_KEY:
        print("❌ Error: JOOBLE_API_KEY is missing.")
        return []
    url = f"https://api.jooble.org/api/{JOOBLE_KEY}"
    try:
        print("📡 Connecting to Jooble API...")
        response = requests.post(url, json={"keywords": "remote", "location": ""}, timeout=15)
        print(f"📊 Jooble Quota Remaining: {response.headers.get('x-ratelimit-remaining', 'N/A')}")
        if response.status_code == 200:
            return response.json().get('jobs', [])
        return []
    except Exception as e:
        print(f"❌ Jooble Fetch Error: {e}")
        return []

def generate_job_page(job):
    """Generates job HTML and returns filename."""
    job_id = job.get('id', '0')
    title = job.get('title', 'job')
    clean_name = re.sub(r'[^a-z0-9]', '-', title.lower())
    filename = f"{clean_name}-{job_id}.html"
    
    # Minimal Job Page (Include your Ads here if needed)
    content = f"<html><head><title>{title} | {job.get('company')} | Job</title></head><body>{job.get('snippet')}</body></html>"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    return filename

def generate_index():
    """Builds the main index.html with Ads and Search Index."""
    print("🏠 Updating Homepage (index.html)...")
    jobs_for_search = []
    job_pattern = re.compile(r".*-(\d{10,})\.html$")
    
    for filename in os.listdir("."):
        if job_pattern.search(filename):
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    content = f.read()
                    match = re.search(r"<title>(.*?) \| (.*?) \|", content)
                    if match:
                        jobs_for_search.append({"t": match.group(1), "c": match.group(2), "u": filename})
            except: continue

    with open("jobs_index.json", "w", encoding="utf-8") as f:
        json.dump(jobs_for_search, f)

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Using your full HTML design from previous steps
    index_template = f"""<!DOCTYPE html><html lang="en"><head>... (Your CSS and layout here) ...</head>
    <body>... (Your 7 Ads and Search logic here) ...</body></html>"""
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(index_template)
    print("✅ index.html and jobs_index.json updated.")

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--generate"
    
    if mode == "--generate":
        jobs = fetch_jobs()
        for job in jobs[:10]:
            fname = generate_job_page(job)
            full_url = f"{SITE_URL}{fname}"
            # THIS IS WHERE IT NOTIFIES GOOGLE
            notify_google(full_url)
        generate_index()
    elif mode == "--index":
        generate_index()

if __name__ == "__main__":
    main()
