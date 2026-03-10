import os
import json
import requests
import datetime
import re
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- CONFIGURATION ---
JOOBLE_KEY = os.environ.get("JOOBLE_API_KEY")
SITE_URL = "https://global-job-hub.github.io/jobs/"
GOOGLE_CREDS = os.environ.get("GOOGLE_CREDENTIALS")
LOG_FILE = "indexing_tracker.json"
MAX_DAILY = 190  # Safety limit (Google's is 200)

def slugify(text):
    """Turns 'Software Engineer' into 'software-engineer' for the URL."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)  # Remove special characters
    return re.sub(r'[-\s]+', '-', text).strip('-')

def get_status():
    """Checks the 'memory' file to see how many we've sent today."""
    today = str(datetime.date.today())
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as f:
                data = json.load(f)
                if data.get("date") == today:
                    return data.get("count", 0), today
        except: pass
    return 0, today

def save_status(count, date):
    """Saves the current count so we don't spam Google."""
    with open(LOG_FILE, "w") as f:
        json.dump({"date": date, "count": count}, f)

def generate_job_page(job):
    """Creates the unique HTML file with the job title in the name."""
    job_id = job.get('id', '0')
    title_slug = slugify(job.get('title', 'job'))
    filename = f"{title_slug}-{job_id}.html" # Example: software-engineer-12345.html
    
    # Get Adsterra codes from GitHub Secrets
    banner_ad = os.environ.get("ADSTERRA_BANNER_CODE", "")
    social_bar = os.environ.get("ADSTERRA_SOCIAL_BAR", "")

    html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{job['title']} - {job['company']} | Global Job Hub</title>
    <style>
        body {{ font-family: sans-serif; line-height: 1.6; max-width: 800px; margin: auto; padding: 20px; background: #f9f9f9; }}
        .card {{ background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .btn {{ display: block; background: #28a745; color: white; text-align: center; padding: 15px; text-decoration: none; border-radius: 5px; font-weight: bold; margin-top: 20px; }}
        .ad {{ margin: 20px 0; text-align: center; }}
    </style>
    <script type="application/ld+json">
    {{
      "@context" : "https://schema.org/",
      "@type" : "JobPosting",
      "title" : "{job['title']}",
      "description" : "{job['snippet']}",
      "hiringOrganization" : {{ "@type" : "Organization", "name" : "{job['company']}" }},
      "jobLocation": {{ "@type": "Place", "address": {{ "@type": "PostalAddress", "addressLocality": "{job['location']}" }} }}
    }}
    </script>
    {social_bar}
</head>
<body>
    <div class="card">
        <h1>{job['title']}</h1>
        <p><strong>Company:</strong> {job['company']} | <strong>Location:</strong> {job['location']}</p>
        <div class="ad">{banner_ad}</div>
        <p>{job['snippet']}</p>
        <a href="{job['link']}" class="btn" target="_blank">Click Here to Apply on Jooble</a>
        <div class="ad">{banner_ad}</div>
    </div>
</body>
</html>
"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_template)
    return filename

def main():
    current_count, today = get_status()
    if current_count >= MAX_DAILY:
        print(f"🛑 Limit Reached for {today}. Stopping.")
        return

    # Fetch Jobs
    url = f"https://jooble.org/api/{JOOBLE_KEY}"
    payload = {{"keywords": "software engineer", "location": "Remote"}}
    res = requests.post(url, json=payload)
    jobs = res.json().get('jobs', [])[:(MAX_DAILY - current_count)]

    if not GOOGLE_CREDS or not jobs:
        print("❌ No jobs found or missing Google Credentials.")
        return

    # Setup Google Indexing
    info = json.loads(GOOGLE_CREDS)
    creds = service_account.Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/indexing"])
    service = build("indexing", "v3", credentials=creds)

    total_now = current_count
    for job in jobs:
        filename = generate_job_page(job)
        full_url = f"{SITE_URL}{filename}"
        
        try:
            body = {{"url": full_url, "type": "URL_UPDATED"}}
            service.urlNotifications().publish(body=body).execute()
            total_now += 1
            print(f"✅ Indexed: {full_url}")
        except Exception as e:
            print(f"⚠️ Error: {e}")

    save_status(total_now, today)

if __name__ == "__main__":
    main()
