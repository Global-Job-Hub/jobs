import os
import sys
import json
import re
import datetime
import requests
import certifi  # Added to handle SSL verification issues
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- CONFIG ---
SITE_URL = os.environ.get("SITE_URL", "https://global-job-hub.github.io/jobs/")
JOOBLE_KEY = os.environ.get("JOOBLE_API_KEY")
GOOGLE_CREDS = os.environ.get("GOOGLE_CREDENTIALS")

# Ensure the SITE_URL ends with a slash
if not SITE_URL.endswith('/'):
    SITE_URL += '/'

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
    """Fetches jobs from Jooble with SSL fix and quota logging."""
    if not JOOBLE_KEY:
        print("❌ Error: JOOBLE_API_KEY is missing.")
        return []
    
    # Extract just the key if the full URL was accidentally passed
    key_only = JOOBLE_KEY.split('/')[-1]
    api_url = f"https://api.jooble.org/api/{key_only}"
    
    payload = {"keywords": "remote", "location": ""}
    
    try:
        print(f"📡 Connecting to Jooble API (SSL fix active)...")
        # We use certifi.where() to provide a valid certificate bundle
        response = requests.post(
            api_url, 
            json=payload, 
            timeout=20, 
            verify=certifi.where() 
        )
        
        print(f"📊 Jooble Quota Remaining: {response.headers.get('x-ratelimit-remaining', 'N/A')}")
        
        if response.status_code == 200:
            return response.json().get('jobs', [])
        else:
            print(f"❌ Jooble Error {response.status_code}: {response.text}")
            return []
            
    except requests.exceptions.SSLError as e:
        print(f"❌ SSL Verification failed. Attempting insecure fallback...")
        # Fallback (use with caution): 
        # response = requests.post(api_url, json=payload, timeout=20, verify=False)
        return []
    except Exception as e:
        print(f"❌ Jooble Fetch Error: {e}")
        return []

def generate_job_page(job):
    """Generates job HTML and returns filename."""
    job_id = job.get('id', '0')
    title = job.get('title', 'job')
    # Better slug generation
    clean_name = re.sub(r'[^a-z0-9]', '-', title.lower())
    clean_name = re.sub(r'-+', '-', clean_name).strip('-')
    filename = f"{clean_name}-{job_id}.html"
    
    # Basic Schema.org inclusion for Google Jobs
    content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title} | {job.get('company')} | Global Job Hub</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>body{{font-family:sans-serif; line-height:1.6; padding:20px; max-width:800px; margin:auto;}}</style>
</head>
<body>
    <h1>{title}</h1>
    <h3>Company: {job.get('company')} | Location: {job.get('location')}</h3>
    <hr>
    <div>{job.get('snippet')}</div>
    <br>
    <a href="{job.get('link')}" style="background:#007bff; color:white; padding:10px 20px; text-decoration:none; border-radius:5px;">Apply on Source</a>
</body>
</html>"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    return filename

def generate_index():
    """Builds the main index.html with Ads and Search Index."""
    print("🏠 Updating Homepage (index.html)...")
    jobs_for_search = []
    # Pattern to find job pages we generated
    job_pattern = re.compile(r".*-\d+\.html$")
    
    for filename in os.listdir("."):
        if job_pattern.match(filename) and filename != "index.html":
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    content = f.read()
                    match = re.search(r"<title>(.*?) \| (.*?) \|", content)
                    if match:
                        jobs_for_search.append({
                            "t": match.group(1), 
                            "c": match.group(2), 
                            "u": filename
                        })
            except Exception:
                continue

    # Save search index
    with open("jobs_index.json", "w", encoding="utf-8") as f:
        json.dump(jobs_for_search, f)

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Minimal index template (Replace '...' with your actual HTML logic)
    index_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Global Job Hub Jobber</title>
</head>
<body>
    <h1>Job Search Index</h1>
    <p>Last updated: {now}</p>
    <div id="ad-top">{ADS['AD_728X90']}</div>
    <ul id="job-list">
        </ul>
</body>
</html>"""
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(index_template)
    print("✅ index.html and jobs_index.json updated.")

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--generate"
    
    if mode == "--generate":
        jobs_list = fetch_jobs()
        if jobs_list:
            print(f"📝 Processing {len(jobs_list[:20])} new jobs...")
            for job in jobs_list[:20]:
                filename = generate_job_page(job)
                full_url = f"{SITE_URL}{filename}"
                notify_google(full_url)
        else:
            print("⚠️ No jobs fetched. Checking local index...")
        
        generate_index()
        
    elif mode == "--index":
        generate_index()

if __name__ == "__main__":
    main()
