import os
import sys
import json
import re
import datetime
import requests
import certifi
import urllib3  # Added to suppress insecure warnings
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- CONFIG ---
SITE_URL = os.environ.get("SITE_URL", "https://global-job-hub.github.io/jobs/")
JOOBLE_KEY = os.environ.get("JOOBLE_API_KEY")
GOOGLE_CREDS = os.environ.get("GOOGLE_CREDENTIALS")

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
    """Fetches jobs from Jooble with a forced bypass for SSL issues."""
    if not JOOBLE_KEY:
        print("❌ Error: JOOBLE_API_KEY is missing.")
        return []
    
    # Extract just the key if the full URL was accidentally passed
    key_only = JOOBLE_KEY.split('/')[-1]
    api_url = f"https://api.jooble.org/api/{key_only}"
    
    try:
        print(f"📡 Connecting to Jooble API (SSL Bypass Enabled)...")
        # Suppress the InsecureRequestWarning in the console
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        response = requests.post(
            api_url, 
            json={"keywords": "remote", "location": ""}, 
            timeout=20, 
            verify=False  # This bypasses the local issuer certificate error
        )
        
        print(f"📊 Jooble Quota Remaining: {response.headers.get('x-ratelimit-remaining', 'N/A')}")
        
        if response.status_code == 200:
            jobs = response.json().get('jobs', [])
            print(f"✅ Successfully fetched {len(jobs)} jobs.")
            return jobs
        else:
            print(f"❌ Jooble Error {response.status_code}: {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ Fatal Fetch Error: {e}")
        return []

def generate_job_page(job):
    """Generates job HTML and returns filename."""
    job_id = job.get('id', '0')
    title = job.get('title', 'job')
    clean_name = re.sub(r'[^a-z0-9]', '-', title.lower())
    clean_name = re.sub(r'-+', '-', clean_name).strip('-')
    filename = f"{clean_name}-{job_id}.html"
    
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

    with open("jobs_index.json", "w", encoding="utf-8") as f:
        json.dump(jobs_for_search, f)

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
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
            print("⚠️ No jobs fetched. Check API Key or Quota above.")
        
        generate_index()
        
    elif mode == "--index":
        generate_index()

if __name__ == "__main__":
    main()
