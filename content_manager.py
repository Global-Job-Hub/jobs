import os
import json
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build

# 1. SETUP CONFIGURATION
# Your GitHub Pages site URL
SITE_URL = "https://global-job-hub.github.io/jobs/"
SCOPES = ["https://www.googleapis.com/auth/indexing"]

def get_google_credentials():
    """Reads the Google JSON key from GitHub Secrets."""
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    if not creds_json:
        print("❌ Error: GOOGLE_CREDENTIALS secret not found!")
        return None
    info = json.loads(creds_json)
    return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)

def notify_google(url):
    """Sends the URL to Google Indexing API."""
    try:
        credentials = get_google_credentials()
        if not credentials:
            return
        
        service = build("indexing", "v3", credentials=credentials)
        body = {
            "url": url,
            "type": "URL_UPDATED"
        }
        
        # This sends the 'publish' request to Google
        result = service.urlNotifications().publish(body=body).execute()
        print(f"✅ Successfully notified Google: {url}")
        print(f"Response: {result}")
    except Exception as e:
        print(f"❌ Failed to notify Google for {url}: {e}")

def main():
    # 2. FIND YOUR JOB FILES
    # This looks for all .html files in your repository (excluding index and privacy)
    job_files = [f for f in os.listdir('.') if f.endswith('.html') and f not in ['index.html', 'privacy.html']]
    
    if not job_files:
        print("ℹ️ No new job files found to index.")
        return

    print(f"🔍 Found {len(job_files)} potential job pages. Submitting to Google...")

    # 3. SUBMIT EACH URL
    # Google free limit is usually 200 URLs per day
    for job_file in job_files[:100]:  # Limits to 100 per run to stay safe
        full_url = f"{SITE_URL}{job_file}"
        notify_google(full_url)

if __name__ == "__main__":
    main()
