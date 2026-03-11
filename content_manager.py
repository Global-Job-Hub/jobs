import os
import sys
import json
import re
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- CONFIG ---
SITE_URL = os.environ.get("SITE_URL", "https://global-job-hub.github.io/jobs/")
GOOGLE_CREDS = os.environ.get("GOOGLE_CREDENTIALS")
EXPIRE_DAYS = 30
HTML_FOLDER = os.environ.get("HTML_FOLDER", "./")
SENT_CACHE_FILE = os.environ.get("SENT_CACHE_FILE", "sent_jobs.json")  # track jobs sent to Google

if not SITE_URL.endswith('/'):
    SITE_URL += '/'

# --- GOOGLE INDEXING API ---
def notify_google(url, action="URL_UPDATED"):
    if not GOOGLE_CREDS:
        print(f"⚠️ Google Indexing skipped: Credentials not found")
        return
    try:
        info = json.loads(GOOGLE_CREDS)
        credentials = service_account.Credentials.from_service_account_info(
            info, scopes=["https://www.googleapis.com/auth/indexing"]
        )
        service = build("indexing", "v3", credentials=credentials)
        body = {"url": url, "type": action}
        service.urlNotifications().publish(body=body).execute()
        print(f"🚀 Google Notified: {url} ({action})")
    except Exception as e:
        print(f"❌ Google Indexing Error: {e}")

# --- HTML GENERATOR ---
def generate_job_page(job):
    job_id = job.get('id', '0')
    title = job.get('title', 'Job')
    clean_name = re.sub(r'[^a-z0-9]', '-', title.lower()).strip('-')
    filename = f"{clean_name}-{job_id}.html"
    filepath = os.path.join(HTML_FOLDER, filename)

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

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filename, filepath

# --- HELPER FUNCTIONS ---
def calculate_expiry(posted_date):
    try:
        dt = datetime.strptime(posted_date, "%Y-%m-%d")
    except:
        dt = datetime.utcnow()
    expiry = dt + timedelta(days=EXPIRE_DAYS)
    return expiry.strftime("%Y-%m-%d")

def load_sent_cache():
    if os.path.exists(SENT_CACHE_FILE):
        with open(SENT_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_sent_cache(cache):
    with open(SENT_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)

def job_hash(job):
    """Generate a hash string based on job content to detect changes"""
    return f"{job.get('title','')}_{job.get('company','')}_{job.get('snippet','')}_{job.get('link','')}"

# --- CLEAN EXPIRED JOBS ---
def remove_expired_html():
    today = datetime.utcnow()
    for filename in os.listdir(HTML_FOLDER):
        if not filename.endswith(".html"):
            continue
        filepath = os.path.join(HTML_FOLDER, filename)
        try:
            mtime = datetime.utcfromtimestamp(os.path.getmtime(filepath))
            expiry_date = mtime + timedelta(days=EXPIRE_DAYS)
            if expiry_date < today:
                os.remove(filepath)
                notify_google(f"{SITE_URL}{filename}", action="URL_DELETED")
                print(f"🗑 Expired page removed: {filename}")
        except Exception as e:
            print(f"⚠ Could not process {filename}: {e}")

# --- MAIN ---
def main():
    if len(sys.argv) < 2:
        print("Usage: python content_manager.py jobs.json")
        sys.exit(1)

    json_file = sys.argv[1]
    with open(json_file, "r", encoding="utf-8") as f:
        jobs_list = json.load(f)

    sent_cache = load_sent_cache()
    updated_cache = sent_cache.copy()

    processed_count = 0

    for job in jobs_list:
        job['expiry_date'] = calculate_expiry(job.get('posted_date', datetime.utcnow().strftime("%Y-%m-%d")))
        h = job_hash(job)

        # Only notify Google if new or changed
        if h in sent_cache and sent_cache[h] == job['expiry_date']:
            print(f"⚡ Skipping unchanged job: {job.get('title')}")
            continue

        filename, filepath = generate_job_page(job)
        notify_google(f"{SITE_URL}{filename}")
        updated_cache[h] = job['expiry_date']
        processed_count += 1

    save_sent_cache(updated_cache)
    print(f"✅ Processed {processed_count} jobs (new or updated)")

    remove_expired_html()
    print("✅ Expired jobs cleaned")

if __name__ == "__main__":
    main()
