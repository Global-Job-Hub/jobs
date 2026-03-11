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

# Get Ads from Environment (GitHub Secrets)
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
    """Sends a single URL to the Google Indexing API and logs the result."""
    if not GOOGLE_CREDS:
        print(f"⚠️ Google Indexing skipped: GOOGLE_CREDENTIALS not set for {url}")
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
        print(f"❌ Google Indexing Error for {url}: {e}")

def fetch_jobs():
    """Fetches jobs from Jooble and prints API health/quota info."""
    if not JOOBLE_KEY:
        print("❌ Error: JOOBLE_API_KEY is not set.")
        return []

    url = f"https://api.jooble.org/api/{JOOBLE_KEY}"
    payload = {"keywords": "remote software developer", "location": ""}
    
    try:
        print("📡 Connecting to Jooble API...")
        response = requests.post(url, json=payload, timeout=15)
        remaining = response.headers.get('x-ratelimit-remaining', 'Not Found')
        print(f"📊 Jooble Quota Status: {remaining}")
        
        if response.status_code == 200:
            data = response.json()
            jobs = data.get('jobs', [])
            print(f"✅ Success: Received {len(jobs)} jobs.")
            return jobs
        return []
    except Exception as e:
        print(f"❌ Jooble Connection failed: {e}")
        return []

def generate_job_page(job):
    """Generates an HTML file for a job and returns the filename."""
    # Create a clean filename
    clean_title = re.sub(r'[^a-zA-Z0-9]', '-', job.get('title', 'job').lower())
    filename = f"{clean_title}-{job.get('id', '000')}.html"
    
    # Placeholder for your actual HTML generation logic
    # Make sure this function actually creates the file!
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"<html><head><title>{job.get('title')} | {job.get('company')} | Job</title></head><body>{job.get('snippet')}</body></html>")
    
    return filename

def generate_index():
    """Reads all current job files and updates index.html."""
    print("🏠 Updating Homepage (index.html)...")
    jobs_for_search = []
    job_pattern = re.compile(r".*-(\d{10,})\.html$")
    
    for filename in os.listdir("."):
        if job_pattern.search(filename):
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    content = f.read()
                    title_match = re.search(r"<title>(.*?) \| (.*?) \|", content)
                    if title_match:
                        jobs_for_search.append({
                            "t": title_match.group(1).strip(),
                            "c": title_match.group(2).strip(),
                            "l": "Remote",
                            "u": filename
                        })
            except Exception as e:
                print(f"⚠️ Error reading {filename}: {e}")

    with open("jobs_index.json", "w", encoding="utf-8") as f:
        json.dump(jobs_for_search, f)

    # Simplified index template for brevity, use your full version here
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    index_html = f"<!DOCTYPE html><html>... (Your Full HTML Template Here) ...</html>"
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(index_html)
    print(f"✅ index.html and jobs_index.json updated.")

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--generate"
    
    if mode == "--generate":
        jobs_list = fetch_jobs()
        if jobs_list:
            for job in jobs_list[:20]:
                filename = generate_job_page(job)
                # Now notify Google about the new page
                full_url = f"{SITE_URL}{filename}"
                notify_google(full_url)
        generate_index()
    elif mode == "--index":
        generate_index()

if __name__ == "__main__":
    main()
