import os
import sys
import json
import requests
import datetime
import time
import re
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- CONFIG ---
SITE_URL = "https://global-job-hub.github.io/jobs/"
JOOBLE_KEY = os.environ.get("JOOBLE_API_KEY")
GOOGLE_CREDS = os.environ.get("GOOGLE_CREDENTIALS")

# Fetch Ad Secrets
AD_728x90 = os.environ.get("AD_728x90", "")
AD_300x250 = os.environ.get("AD_300x250", "")
AD_468x60 = os.environ.get("AD_468x60", "")
AD_160x600 = os.environ.get("AD_160x600", "")
AD_160x300 = os.environ.get("AD_160x300", "")
AD_320x50 = os.environ.get("AD_320x50", "")
AD_NATIVE = os.environ.get("AD_NATIVE", "")

def slugify(text):
    text = str(text).lower()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[-\s]+', '-', text).strip('-')

def notify_google_indexing(url, action="URL_UPDATED"):
    if not GOOGLE_CREDS: return
    try:
        info = json.loads(GOOGLE_CREDS)
        creds = service_account.Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/indexing"])
        service = build("indexing", "v3", credentials=creds)
        service.urlNotifications().publish(body={"url": url, "type": action}).execute()
        print(f"📡 Google Notified ({action}): {url}")
    except Exception as e:
        print(f"⚠️ Google Indexing Failed: {e}")

def cleanup_expired_jobs():
    print("🧹 Scanning for expired listings...")
    today = datetime.date.today().isoformat()
    for filename in os.listdir("."):
        if filename.endswith(".html") and "-" in filename:
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    content = f.read()
                match = re.search(r'"validThrough"\s*:\s*"(\d{4}-\d{2}-\d{2})', content)
                if match and today > match.group(1):
                    notify_google_indexing(f"{SITE_URL}{filename}", "URL_DELETED")
                    os.remove(filename)
                    print(f"🗑️ Deleted expired: {filename}")
            except: pass

def generate_job_page(job):
    job_id = job.get('id', '0')
    title = job.get('title', 'Job Opening')
    company = job.get('company', 'Hiring Company')
    location = job.get('location', 'Remote')
    snippet = job.get('snippet', '').replace('"', "'")
    link = job.get('link', '#')
    
    title_slug = slugify(title)
    filename = f"{title_slug}-{job_id}.html"

    # --- UNIQUE CHECK ---
    if os.path.exists(filename):
        print(f"⏭️ Skipping (Already Exists): {filename}")
        return None 

    updated_raw = job.get('updated', datetime.datetime.now().isoformat())
    post_date = updated_raw.split('T')[0] 
    expiry_date = (datetime.datetime.strptime(post_date, "%Y-%m-%d").date() + datetime.timedelta(days=30)).isoformat()
    
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | {company} - Job Details</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; background: #f4f7f9; margin: 0; padding: 0; color: #333; }}
        .ad-row {{ text-align: center; padding: 10px; background: #fff; border-bottom: 1px solid #eee; }}
        .main-layout {{ display: flex; justify-content: center; gap: 20px; padding: 20px; max-width: 1200px; margin: 0 auto; }}
        .skyscraper {{ width: 160px; flex-shrink: 0; display: none; }}
        @media (min-width: 1000px) {{ .skyscraper {{ display: block; }} }}
        .wrapper {{ flex-grow: 1; max-width: 800px; background: #fff; border-radius: 12px; box-shadow: 0 5px 15px rgba(0,0,0,0.05); overflow: hidden; border: 1px solid #e1e4e8; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 18px 25px; text-align: left; border-bottom: 1px solid #f0f0f0; }}
        th {{ background: #f9f9f9; width: 30%; color: #666; font-size: 12px; text-transform: uppercase; }}
        .apply-btn {{ background: #28a745; color: #fff; padding: 15px 30px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block; }}
        .more-jobs-row {{ background: #eef6ff; text-align: center; padding: 20px; }}
        .more-jobs-btn {{ color: #007bff; font-weight: bold; text-decoration: none; border: 2px solid #007bff; padding: 8px 20px; border-radius: 20px; }}
        .sticky-footer {{ position: fixed; bottom: 0; width: 100%; background: #fff; border-top: 1px solid #ddd; text-align: center; padding: 5px 0; z-index: 1000; }}
    </style>
</head>
<body>
<div class="ad-row">{AD_728x90}</div>
<div class="main-layout">
    <aside class="skyscraper">{AD_160x600}</aside>
    <div class="wrapper">
        <table>
            <tr><th>Job Title</th><td><h2 style="margin:0; color:#007bff;">{title}</h2></td></tr>
            <tr><td colspan="2" class="ad-row">{AD_468x60}</td></tr>
            <tr><th>Company</th><td>{company}</td></tr>
            <tr><th>Location</th><td>{location}, US</td></tr>
            <tr><td colspan="2" class="ad-row">{AD_NATIVE}</td></tr>
            <tr><th>Description</th><td>{snippet}</td></tr>
            <tr><td colspan="2" class="ad-row">{AD_300x250}</td></tr>
            <tr><th>Action</th><td><a href="{link}" class="apply-btn" target="_blank">Apply Now &raquo;</a></td></tr>
        </table>
        <div class="more-jobs-row">
            <p style="margin-bottom:15px;">Looking for something else?</p>
            <a href="{SITE_URL}" class="more-jobs-btn">View More Jobs</a>
        </div>
    </div>
    <aside class="skyscraper">{AD_160x300}</aside>
</div>
<div class="sticky-footer">{AD_320x50}</div>
<footer style="text-align:center; padding:40px; color:#999; font-size:12px; margin-bottom:60px;">© 2026 Global Job Hub</footer>
</body>
</html>"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_template)
    return filename

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--generate"
    
    if mode == "--generate":
        print("🚀 Starting generation process...")
        if not JOOBLE_KEY: return
            
        url = f"https://jooble.org/api/{JOOBLE_KEY}"
        res = requests.post(url, json={"keywords": "remote", "location": ""})
        jobs = res.json().get('jobs', [])
        
        new_urls = []
        all_jobs_data = [] 
        unique_count = 0
        
        for job in jobs:
            # Generate the page. Returns filename if NEW, None if DUPLICATE.
            fname = generate_job_page(job)
            
            if fname:
                new_urls.append(f"{SITE_URL}{fname}")
                unique_count += 1
            
            # Use the slugified name for the search index regardless to keep it updated
            title_slug = slugify(job.get('title'))
            actual_fname = f"{title_slug}-{job.get('id')}.html"
            all_jobs_data.append({"t": job.get('title'), "c": job.get('company'), "l": job.get('location'), "u": actual_fname})

            if unique_count >= 20: break # Keep only 20 fresh unique ones per run

        # Save search index
        with open("jobs_index.json", "w", encoding="utf-8") as f:
            json.dump(all_jobs_data, f)
            
        # Home Page Injection
        if os.path.exists("index_template.html"):
            with open("index_template.html", "r", encoding="utf-8") as f:
                home_html = f.read()
            for ad in ["AD_728x90", "AD_300x250", "AD_468x60", "AD_160x600", "AD_160x300", "AD_320x50", "AD_NATIVE"]:
                home_html = home_html.replace(f"{{{{{ad}}}}}", os.environ.get(ad, ""))
            with open("index.html", "w", encoding="utf-8") as f:
                f.write(home_html)

        # Write only the NEWly created URLs for Google Indexing
        with open("pending_urls.txt", "w") as f:
            for u in new_urls: f.write(u + "\n")
            
        print(f"✅ Created {unique_count} NEW unique jobs. Total in index: {len(all_jobs_data)}")

    elif mode == "--cleanup":
        cleanup_expired_jobs()
    
    elif mode == "--index":
        if not os.path.exists("pending_urls.txt"):
            print("ℹ️ No pending URLs to index.")
            return
            
        print("🔗 Starting Google Indexing process...")
        with open("pending_urls.txt", "r") as f:
            urls = f.readlines()
            
        for url in urls:
            url = url.strip()
            if url:
                notify_google_indexing(url, "URL_UPDATED")
                time.sleep(1) # Small delay to respect API limits

if __name__ == "__main__":
    main()
