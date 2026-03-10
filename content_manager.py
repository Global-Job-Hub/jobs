import os
import json
import requests
import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- CONFIGURATION ---
JOOBLE_KEY = os.environ.get("JOOBLE_API_KEY")
SITE_URL = "https://global-job-hub.github.io/jobs/"
GOOGLE_CREDS = os.environ.get("GOOGLE_CREDENTIALS")
LOG_FILE = "indexing_tracker.json"
MAX_DAILY = 195  # Staying just under 200 to be safe

def get_status():
    """Reads the current count and date from the tracker file."""
    today = str(datetime.date.today())
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as f:
                data = json.load(f)
                if data.get("date") == today:
                    return data.get("count", 0), today
        except:
            pass
    return 0, today

def save_status(count, date):
    """Saves the updated count and date."""
    with open(LOG_FILE, "w") as f:
        json.dump({"date": date, "count": count}, f)

def main():
    current_count, today = get_status()
    
    # 1. THE AUTO-CHECK
    if current_count >= MAX_DAILY:
        print(f"🛑 STOP: You have already indexed {current_count} pages today ({today}).")
        print("To avoid Google API bans, no more requests will be sent until tomorrow.")
        return

    # 2. FETCH JOBS
    # (Assuming you use Jooble to get new job data)
    print(f"🔄 Starting run. Current daily total: {current_count}")
    
    # Example logic: only fetch what we have space for
    space_left = MAX_DAILY - current_count
    
    # --- FETCH JOBS FROM JOOBLE ---
    # (Abbreviated fetch logic for clarity)
    url = f"https://jooble.org/api/{JOOBLE_KEY}"
    payload = {"keywords": "software engineer", "location": "Remote"}
    res = requests.post(url, json=payload)
    jobs = res.json().get('jobs', [])[:space_left] # Only take what's allowed

    if not jobs:
        print("✅ No new jobs to process.")
        return

    # 3. INITIALIZE GOOGLE API
    info = json.loads(GOOGLE_CREDS)
    creds = service_account.Credentials.from_service_account_info(
        info, scopes=["https://www.googleapis.com/auth/indexing"]
    )
    service = build("indexing", "v3", credentials=creds)

    new_indexed_count = current_count
    for job in jobs:
        # 4. GENERATE PAGE & SEND TO GOOGLE
        # ... (Insert your page generation logic here) ...
        
        job_url = f"{SITE_URL}job-{job['id']}.html" # Example URL
        
        try:
            body = {"url": job_url, "type": "URL_UPDATED"}
            service.urlNotifications().publish(body=body).execute()
            new_indexed_count += 1
            print(f"✅ Indexed: {job_url}")
        except Exception as e:
            print(f"⚠️ Error indexing {job_url}: {e}")

    # 5. SAVE PROGRESS
    save_status(new_indexed_count, today)
    print(f"📊 Run finished. Total indexed for today: {new_indexed_count}")

if __name__ == "__main__":
    main()
