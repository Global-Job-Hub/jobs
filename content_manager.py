import os
import sys
import json
import re
import datetime
import requests
import urllib3
from google.oauth2 import service_account
from googleapiclient.discovery import build
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- CONFIG ---
SITE_URL = os.environ.get("SITE_URL", "https://global-job-hub.github.io/jobs/")
GOOGLE_CREDS = os.environ.get("GOOGLE_CREDENTIALS")

if not SITE_URL.endswith('/'):
    SITE_URL += '/'

def notify_google(url):
    """Notifies Google Indexing API about a new/updated job URL."""
    if not GOOGLE_CREDS:
        print(f"⚠️ Google Indexing skipped: Credentials secret not found.")
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
    """Fetches jobs from We Work Remotely (WWR) and maps them to the internal format."""
    api_url = "https://weworkremotely.com/api/v1/remote-jobs"
    
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    session.mount("https://", HTTPAdapter(max_retries=retry_strategy))

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        print(f"📡 Connecting to We Work Remotely API...")
        response = session.get(api_url, headers=headers, timeout=20)

        if response.status_code == 200:
            raw_data = response.json()
            raw_jobs = raw_data.get('jobs', [])
            
            # --- DATA MAPPING ---
            # Transform WWR fields to match your existing 'generate_job_page' logic
            formatted_jobs = []
            for job in raw_jobs:
                formatted_jobs.append({
                    'id': job.get('id'),
                    'title': job.get('title'),
                    'company': job.get('company'),
                    'snippet': job.get('description'), # WWR uses 'description' instead of 'snippet'
                    'link': job.get('url')              # WWR uses 'url' instead of 'link'
                })
            
            print(f"✅ Success! Fetched {len(formatted_jobs)} jobs from WWR.")
            return formatted_jobs
        else:
            print(f"❌ WWR Error {response.status_code}: {response.text[:100]}")
            
    except Exception as e:
        print(f"❌ Fatal Fetch Error: {e}")
        
    return []

def generate_job_page(job):
    """Generates a standalone HTML page for a specific job."""
    job_id = job.get('id', '0')
    title = job.get('title', 'job')
    # Create a URL-friendly slug
    clean_name = re.sub(r'[^a-z0-9]', '-', title.lower()).strip('-')
    filename = f"{clean_name}-{job_id}.html"
    
    # Using .get() ensures the script doesn't crash if a field is missing
    content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | {job.get('company')}</title>
    <style>
        body{{font-family:sans-serif; padding:40px; line-height:1.6; max-width:800px; margin:auto;}}
        .btn {{background:#007bff; color:#fff; padding:12px 20px; text-decoration:none; border-radius:5px; display:inline-block;}}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <p><strong>Company:</strong> {job.get('company')}</p>
    <hr>
    <div>{job.get('snippet')}</div>
    <br><br>
    <a href="{job.get('link')}" class="btn">View Full Job Posting</a>
</body>
</html>"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    return filename

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--generate"
    
    if mode == "--generate":
        jobs_list = fetch_jobs()
        if jobs_list:
            # Limit to 20 jobs to respect Google Indexing limits and build times
            to_process = jobs_list[:20]
            for job in to_process:
                filename = generate_job_page(job)
                notify_google(f"{SITE_URL}{filename}")
            print(f"✅ Processed {len(to_process)} jobs.")
        else:
            print("⚠️ No jobs processed. Check API connection.")

if __name__ == "__main__":
    main()
