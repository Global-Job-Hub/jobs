import os
import sys
import json
import re
import datetime
import requests
import urllib3
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- CONFIG FROM SECRETS ---
# SITE_URL: https://global-job-hub.github.io/jobs/
SITE_URL = os.environ.get("SITE_URL", "https://global-job-hub.github.io/jobs/")
# JOOBLE_API_KEY: Should be just the hex code (e.g., 550e8400-...)
RAW_KEY = os.environ.get("JOOBLE_API_KEY", "")
# GOOGLE_CREDENTIALS: The full JSON string from your service account
GOOGLE_CREDS = os.environ.get("GOOGLE_CREDENTIALS")

# --- CLEANING LOGIC ---
# This ensures that even if you pasted "https://api.jooble.org/api/KEY", 
# the script extracts ONLY the "KEY" part.
JOOBLE_KEY = RAW_KEY.strip().split('/')[-1]

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

import requests
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def fetch_jobs():
    """Fetches jobs from Jooble with robust error handling for IP bans and SSL issues."""
    if not JOOBLE_KEY:
        print("❌ CRITICAL ERROR: JOOBLE_API_KEY secret is empty or missing!")
        return []

    api_url = f"https://jooble.org/api/v2/{JOOBLE_KEY}"
    
    # 1. Setup a robust Session with Retries
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1, # Waits 1s, 2s, 4s between retries
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)

    # 2. Add a realistic User-Agent to avoid IP/Bot bans
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    payload = {
        "keywords": "remote", 
        "location": "",
        "searchMode": 1 
    }

    try:
        print(f"📡 Connecting to Jooble API...")
        
        # Note: Keeping verify=True is safer. If you get SSL errors, 
        # ensure your 'certifi' package is updated: pip install --upgrade certifi
        response = session.post(
            api_url, 
            json=payload, 
            headers=headers,
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()
            jobs = data.get('jobs', [])
            print(f"✅ Success! Fetched {len(jobs)} jobs.")
            return jobs
            
        elif response.status_code == 403:
            print("❌ Error 403: Forbidden. Your IP might be temporarily throttled or blocked.")
        elif response.status_code == 429:
            print("❌ Error 429: Rate limit exceeded.")
        else:
            print(f"❌ Server returned status {response.status_code}")
            
        return []
            
    except requests.exceptions.SSLError as ssl_err:
        print(f"🔐 SSL Handshake Error: {ssl_err}. Try updating certifi or checking system clock.")
    except requests.exceptions.ConnectionError as conn_err:
        print(f"🌐 Connection Error: {conn_err}. Check your internet or VPN/Proxy settings.")
    except Exception as e:
        print(f"❌ Fatal Error: {e}")
    
    return []

def generate_job_page(job):
    """Generates a standalone HTML page for a specific job."""
    job_id = job.get('id', '0')
    title = job.get('title', 'job')
    # Create a URL-friendly slug
    clean_name = re.sub(r'[^a-z0-9]', '-', title.lower()).strip('-')
    filename = f"{clean_name}-{job_id}.html"
    
    content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title} | {job.get('company')}</title>
    <style>body{{font-family:sans-serif; padding:40px; line-height:1.6;}}</style>
</head>
<body>
    <h1>{title}</h1>
    <p><strong>Company:</strong> {job.get('company')}</p>
    <hr>
    <div>{job.get('snippet')}</div>
    <br>
    <a href="{job.get('link')}" style="background:#007bff; color:#fff; padding:10px; text-decoration:none;">View Full Job</a>
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
            # Process the first 20 jobs to avoid hitting Google's daily indexing limit
            for job in jobs_list[:20]:
                filename = generate_job_page(job)
                notify_google(f"{SITE_URL}{filename}")
            print(f"✅ Processed {len(jobs_list[:20])} jobs.")
        else:
            print("⚠️ No jobs processed. Check API Quota or Key.")

if __name__ == "__main__":
    main()
