import os
import sys
import json
import requests
import datetime
import re
import hashlib
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- CONFIG ---
SITE_URL = "https://global-job-hub.github.io/jobs/"
JOOBLE_KEY = os.environ.get("JOOBLE_API_KEY")
GOOGLE_CREDS = os.environ.get("GOOGLE_CREDENTIALS")

ADS = {
    "AD_728x90": os.environ.get("AD_728x90", ""),
    "AD_300x250": os.environ.get("AD_300x250", ""),
    "AD_468x60": os.environ.get("AD_468x60", ""),
    "AD_160x600": os.environ.get("AD_160x600", ""),
    "AD_160x300": os.environ.get("AD_160x300", ""),
    "AD_320x50": os.environ.get("AD_320x50", ""),
    "AD_NATIVE": os.environ.get("AD_NATIVE", "")
}

# 1. HELPER FUNCTIONS
def get_ultra_sensitive_hash(job):
    job_string = json.dumps(job, sort_keys=True)
    return hashlib.sha256(job_string.encode('utf-8')).hexdigest()

def slugify(text):
    text = str(text).lower()
    return re.sub(r'[-\s]+', '-', re.sub(r'[^\w\s-]', '', text)).strip('-')

def notify_google(url, action="URL_UPDATED"):
    if not GOOGLE_CREDS:
        print(f"⚠️ No Google Creds for: {url}")
        return
    try:
        info = json.loads(GOOGLE_CREDS)
        creds = service_account.Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/indexing"])
        service = build("indexing", "v3", credentials=creds)
        service.urlNotifications().publish(body={"url": url, "type": action}).execute()
        print(f"📡 Google Notified ({action}): {url}")
    except Exception as e:
        print(f"❌ Indexing Error: {e}")

# 2. THE CORE GENERATOR
def generate_job_page(job):
    job_id = job.get('id', '0')
    title = job.get('title', 'Job Opening')
    company = job.get('company', 'Hiring Company')
    location = job.get('location', 'Remote')
    salary = job.get('salary', 'Competitive')
    snippet = job.get('snippet', '').replace('"', "'")
    link = job.get('link', '#')
    
    new_hash = get_ultra_sensitive_hash(job)
    filename = f"{slugify(title)}-{job_id}.html"
    expiry_date = (datetime.date.today() + datetime.timedelta(days=30)).isoformat()
    post_date = datetime.date.today().isoformat()

    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            if f"DATA_HASH:{new_hash}" in f.read():
                return None 

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} at {company}</title>
    <style>
        body {{ font-family: 'Inter', sans-serif; background: #f0f2f5; margin: 0; }}
        .header-ad {{ background: #fff; padding: 15px; text-align: center; border-bottom: 1px solid #ddd; }}
        .layout {{ display: flex; max-width: 1250px; margin: 25px auto; gap: 20px; padding: 0 15px; }}
        .skyscraper {{ width: 160px; flex-shrink: 0; position: sticky; top: 20px; height: 600px; }}
        .main-card {{ flex-grow: 1; background: #fff; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #e1e4e8; overflow: hidden; }}
        .job-hero {{ padding: 35px; background: #fff; border-bottom: 1px solid #eee; }}
        .meta-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; padding: 25px; background: #fafafa; }}
        .description-area {{ padding: 35px; line-height: 1.7; }}
        .btn-apply {{ background: #28a745; color: #fff; padding: 15px 40px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block; }}
        .footer-ad {{ position: fixed; bottom: 0; width: 100%; background: #fff; border-top: 1px solid #ddd; text-align: center; padding: 5px 0; }}
        @media (max-width: 1000px) {{ .skyscraper {{ display: none; }} }}
    </style>
</head>
<body>
    <div class="header-ad">{ADS['AD_728x90']}</div>
    <div class="layout">
        <aside class="skyscraper">{ADS['AD_160x600']}</aside>
        <main class="main-card">
            <div class="job-hero"><h1>{title}</h1><p>{company}</p></div>
            <div class="header-ad">{ADS['AD_468x60']}</div>
            <div class="meta-grid">
                <div><strong>Location:</strong> {location}</div>
                <div><strong>Salary:</strong> {salary}</div>
                <div><strong>Posted:</strong> {post_date}</div>
            </div>
            <div class="description-area">{snippet}</div>
            <div class="header-ad">{ADS['AD_300x250']}</div>
            <div style="text-align:center; padding: 40px;"><a href="{link}" class="btn-apply" target="_blank">Apply Now</a></div>
        </main>
        <aside class="skyscraper">{ADS['AD_160x300']}</aside>
    </div>
    <div class="footer-ad">{ADS['AD_320x50']}</div>
</body>
</html>"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_template)
    return filename

# 3. CLEANUP LOGIC
def cleanup_numeric_jobs():
    print("🧹 Cleaning expired jobs...")
    today = datetime.date.today().isoformat()
    job_pattern = re.compile(r"-(\d{10,})\.html$")
    for filename in os.listdir("."):
        if job_pattern.search(filename):
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    content = f.read()
                match = re.search(r'', content)
                if match and today > match.group(1):
                    print(f"🗑️ Deleting {filename}")
                    notify_google(f"{SITE_URL}{filename}", "URL_DELETED")
                    os.remove(filename)
            except: pass

# 4. MAIN RUNNER
def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--generate"
    
    if mode == "--generate":
        if not JOOBLE_KEY: return
        res = requests.post(f"https://jooble.org/api/{JOOBLE_KEY}", json={"keywords": "remote", "location": ""})
        jobs = res.json().get('jobs', [])
        
        new_urls = []
        for job in jobs[:20]:
            fname = generate_job_page(job)
            if fname:
                new_urls.append(f"{SITE_URL}{fname}")
        
        with open("pending_urls.txt", "w") as f:
            for u in new_urls: f.write(u + "\n")
            
    elif mode == "--index":
        if os.path.exists("pending_urls.txt"):
            with open("pending_urls.txt", "r") as f:
                for url in f.read().splitlines():
                    notify_google(url, "URL_UPDATED")
            os.remove("pending_urls.txt")

    elif mode == "--cleanup":
        cleanup_numeric_jobs()

if __name__ == "__main__":
    main()
