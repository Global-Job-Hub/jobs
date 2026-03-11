import os
import sys
import json
import re
import time
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- CONFIG ---
SITE_URL = os.getenv("SITE_URL", "https://global-job-hub.github.io/jobs/")
SENT_URLS_FILE = "sent_urls.json"
INDEX_FILE = "index.json"
GENERATED_URLS_FILE = "generated_urls.json"
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "service_account.json")

# --- Ads ---
AD_160X300 = os.getenv('AD_160X300', '<div class="ad-slot-placeholder">Ad 160x300</div>')
AD_160X600 = os.getenv('AD_160X600', '<div class="ad-slot-placeholder">Ad 160x600</div>')
AD_300X250 = os.getenv('AD_300X250', '<div class="ad-slot-placeholder">Ad 300x250</div>')
AD_320X50  = os.getenv('AD_320X50',  '<div class="ad-slot-placeholder">Ad 320x50</div>')
AD_468X60  = os.getenv('AD_468X60',  '<div class="ad-slot-placeholder">Ad 468x60</div>')
AD_728X90  = os.getenv('AD_728X90',  '<div class="ad-slot-placeholder">Ad 728x90</div>')
AD_NATIVE  = os.getenv('AD_NATIVE',  '<div class="ad-slot-placeholder">Native Ad</div>')

# --- Helpers ---
def slugify(text):
    text = str(text).lower()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[-\s]+', '-', text).strip('-')

def load_json_file(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_json_file(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def load_sent_urls():
    return set(load_json_file(SENT_URLS_FILE))

def save_sent_urls(urls):
    save_json_file(SENT_URLS_FILE, list(urls))

# --- Generate HTML page ---
def generate_job_page(job):
    job_id = job.get('id', '0')
    title = job.get('title', 'Job Opening')
    company = job.get('company_name', 'Hiring Company')
    loc_data = job.get('job_location', {}).get('address', {})
    city = loc_data.get('addressLocality', 'Remote')
    country = loc_data.get('addressCountry', 'US')
    location_str = f"{city}, {country}"
    description = job.get('description', '').replace('"', "'")
    apply_url = job.get('apply_url', '#')
    post_date = job.get('date_posted', datetime.utcnow().strftime("%Y-%m-%d"))
    valid_through = job.get('valid_through', (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d"))
    title_slug = slugify(title)
    filename = f"{title_slug}-{job_id}.html"

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | {company}</title>
<style>
body {{ font-family:sans-serif; background:#f0f2f5; margin:0; padding:20px; }}
.main-container {{ max-width:900px; margin:0 auto; background:#fff; padding:20px; border-radius:10px; }}
.ad-section {{ padding:15px; text-align:center; border:1px solid #eee; margin:10px 0; }}
</style>
</head>
<body>
<div class="main-container">
<h1>{title}</h1>
<p><strong>{company}</strong> • {location_str}</p>
<div class="ad-section">{AD_728X90}</div>
<p>{description}</p>
<div class="ad-section">{AD_NATIVE}</div>
<p><a href="{apply_url}" target="_blank">Apply Now</a></p>
<div class="ad-section">{AD_300X250}</div>
</div>
</body>
</html>"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_template)

    return filename, {
        "id": job_id,
        "title": title,
        "company": company,
        "location": location_str,
        "url": f"{SITE_URL}{filename}",
        "date_posted": post_date
    }

# --- Google Indexing ---
def send_to_google_indexing(urls):
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        print(f"Google Service Account JSON not found at {SERVICE_ACCOUNT_FILE}. Skipping indexing.")
        return set()
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=['https://www.googleapis.com/auth/indexing'])
    service = build('indexing', 'v3', credentials=credentials)
    sent = set()
    for url in urls:
        try:
            service.urlNotifications().publish(body={"url": url, "type": "URL_UPDATED"}).execute()
            print(f"Sent URL to Google: {url}")
            sent.add(url)
            time.sleep(1)
        except Exception as e:
            print(f"Failed to send {url}: {e}")
    return sent

# --- Main ---
def main():
    if len(sys.argv) < 2:
        print("Usage: python content_manager.py jobs.json")
        sys.exit(1)

    input_file = sys.argv[1]
    if not os.path.exists(input_file):
        print(f"File '{input_file}' not found.")
        sys.exit(1)

    print(f"Loading jobs from {input_file}...")
    with open(input_file, "r", encoding="utf-8") as f:
        jobs_list = json.load(f)

    generated_urls = []
    index_data = load_json_file(INDEX_FILE)
    sent_urls = load_sent_urls()

    for job in jobs_list:
        filename, job_entry = generate_job_page(job)
        generated_urls.append(job_entry["url"])
        print(f"Created: {filename}")
        if not any(j["url"] == job_entry["url"] for j in index_data):
            index_data.append(job_entry)

    # Save all JSON files (always)
    save_json_file(INDEX_FILE, index_data)
    save_json_file(GENERATED_URLS_FILE, generated_urls)
    save_sent_urls(sent_urls)  # ensures sent_urls.json exists

    # Determine new URLs to send
    new_urls = [url for url in generated_urls if url not in sent_urls]
    if new_urls:
        sent_now = send_to_google_indexing(new_urls)
        sent_urls.update(sent_now)
        save_sent_urls(sent_urls)

    # Pending URLs
    with open("pending_urls.txt", "w", encoding="utf-8") as f:
        for url in generated_urls:
            f.write(url + "\n")

    print(f"Finished. {len(generated_urls)} job pages generated.")

if __name__ == "__main__":
    main()
