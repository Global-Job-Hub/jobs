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
HTML_FOLDER = os.environ.get("HTML_FOLDER", "./")
SENT_CACHE_FILE = os.environ.get("SENT_CACHE_FILE", "sent_jobs.json")

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
    title = job.get('title', 'Job Opening')
    # Use 'company_name' from your new JSON structure
    company = job.get('company_name', 'Unknown Company')
    # Use 'description' from your new JSON structure
    description = job.get('description', 'No description provided.')
    # Use 'apply_url' from your new JSON structure
    apply_url = job.get('apply_url', '#')
    
    clean_name = re.sub(r'[^a-z0-9]', '-', title.lower()).strip('-')
    filename = f"{clean_name}-{job_id}.html"
    filepath = os.path.join(HTML_FOLDER, filename)

    # Added JSON-LD for Google Jobs SEO
    schema_json = {
        "@context": "https://schema.org/",
        "@type": "JobPosting",
        "title": title,
        "description": description,
        "hiringOrganization": {"@type": "Organization", "name": company},
        "datePosted": job.get("date_posted", datetime.utcnow().strftime("%Y-%m-%d")),
        "validThrough": job.get("valid_through"),
        "employmentType": job.get("employment_type", "FULL_TIME"),
        "jobLocation": {"@type": "Place", "address": job.get("job_location", {}).get("address")}
    }

    content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | {company}</title>
    <script type="application/ld+json">
    {json.dumps(schema_json)}
    </script>
    <style>
        body{{font-family:sans-serif; padding:40px; line-height:1.6; max-width:800px; margin:auto; color:#333;}}
        .btn {{background:#007bff; color:#fff; padding:15px 25px; text-decoration:none; border-radius:5px; display:inline-block; font-weight:bold;}}
        .company-tag {{color:#666; font-size:1.1em; margin-bottom:20px;}}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <p class="company-tag"><strong>Company:</strong> {company}</p>
    <hr>
    <div class="job-desc">
        {description}
    </div>
    <br><br>
    <a href="{apply_url}" class="btn">Apply for this Job</a>
</body>
</html>"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filename, filepath

# --- CACHE HELPERS ---
def load_sent_cache():
    if os.path.exists(SENT_CACHE_FILE):
        with open(SENT_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_sent_cache(cache):
    with open(SENT_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)

def job_hash(job):
    """Detects changes in the manual data provided"""
    return f"{job.get('title')}_{job.get('company_name')}_{job.get('apply_url')}"

# --- MAIN ---
def main():
    if len(sys.argv) < 2:
        print("Usage: python content_manager.py manual_jobs.json")
        sys.exit(1)

    json_file = sys.argv[1]
    with open(json_file, "r", encoding="utf-8") as f:
        jobs_list = json.load(f)

    sent_cache = load_sent_cache()
    updated_cache = sent_cache.copy()
    processed_count = 0

    for job in jobs_list:
        h = job_hash(job)
        expiry = job.get('valid_through', 'N/A')

        # Only process if new or changed
        if h in sent_cache and sent_cache[h] == expiry:
            print(f"⚡ Skipping unchanged job: {job.get('title')}")
            continue

        filename, filepath = generate_job_page(job)
        
        # Send the generated URL to Google
        notify_google(f"{SITE_URL}{filename}")
        
        updated_cache[h] = expiry
        processed_count += 1

    save_sent_cache(updated_cache)
    print(f"✅ Finished! Processed {processed_count} jobs.")

if __name__ == "__main__":
    main()
