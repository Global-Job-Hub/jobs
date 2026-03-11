import os
import sys
import json
import re
import time
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- SCRIPT DIRECTORY ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# --- CONFIG ---
SITE_URL = "https://global-job-hub.github.io/jobs/"
SENT_URLS_FILE = os.path.join(SCRIPT_DIR, "sent_urls.json")
INDEX_FILE = os.path.join(SCRIPT_DIR, "index.json")
GENERATED_URLS_FILE = os.path.join(SCRIPT_DIR, "generated_urls.json")
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", os.path.join(SCRIPT_DIR, "service_account.json"))

# --- Ads ---
AD_160X300 = os.getenv('AD_160X300', '<div class="ad-slot-placeholder">Ad 160x300</div>')
AD_160X600 = os.getenv('AD_160X600', '<div class="ad-slot-placeholder">Ad 160x600</div>')
AD_300X250 = os.getenv('AD_300X250', '<div class="ad-slot-placeholder">Ad 300x250</div>')
AD_320X50  = os.getenv('AD_320X50',  '<div class="ad-slot-placeholder">Ad 320x50</div>')
AD_468X60  = os.getenv('AD_468X60',  '<div class="ad-slot-placeholder">Ad 468x60</div>')
AD_728X90  = os.getenv('AD_728X90',  '<div class="ad-slot-placeholder">Ad 728x90</div>')
AD_NATIVE  = os.getenv('AD_NATIVE',  '<div class="ad-slot-placeholder">Native Ad</div>')

# --- Helper functions ---
def slugify(text):
    text = str(text).lower()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[-\s]+', '-', text).strip('-')

def load_json_file(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_json_file(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def load_sent_urls():
    # Ensure we return a set for easy comparison
    data = load_json_file(SENT_URLS_FILE)
    return set(data) if isinstance(data, list) else set()

def save_sent_urls(url_set):
    # Convert set back to list for JSON storage
    save_json_file(SENT_URLS_FILE, list(url_set))

# --- Generate individual job page ---
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
.apply-btn {{ display:inline-block; padding:15px 30px; background:#28a745; color:#fff; text-decoration:none; border-radius:5px; }}
.apply-btn:hover {{ background:#218838; }}
</style>
</head>
<body>
<div class="main-container">
<h1>{title}</h1>
<p><strong>{company}</strong> • {location_str}</p>
<div class="ad-section">{AD_728X90}</div>
<p>{description}</p>
<div class="ad-section">{AD_NATIVE}</div>
<p><a href="{apply_url}" target="_blank" class="apply-btn">Apply Now</a></p>
<div class="ad-section">{AD_300X250}</div>
</div>
</body>
</html>"""

    with open(os.path.join(SCRIPT_DIR, filename), "w", encoding="utf-8") as f:
        f.write(html_template)

    return filename, {
        "id": job_id,
        "title": title,
        "company": company,
        "location": location_str,
        "url": f"{SITE_URL}{filename}",
        "date_posted": post_date
    }

# --- Send URLs to Google Indexing API ---
def send_to_google_indexing(urls):
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        print(f"Service Account not found. URLs will be marked as 'tracked' but not sent to Google.")
        return set() # Return empty set so we don't crash, but script continues
    
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=['https://www.googleapis.com/auth/indexing'])
    service = build('indexing', 'v3', credentials=credentials)
    
    sent = set()
    for url in urls:
        try:
            service.urlNotifications().publish(body={"url": url, "type": "URL_UPDATED"}).execute()
            print(f"Successfully Indexed: {url}")
            sent.add(url)
            time.sleep(1) # Respect rate limits
        except Exception as e:
            print(f"Indexing failed for {url}: {e}")
    return sent

# --- MAIN ---
def main():
    if len(sys.argv) < 2:
        print("Usage: python content_manager.py jobs.json")
        sys.exit(1)

    input_file = sys.argv[1]
    if not os.path.exists(input_file):
        print(f"File '{input_file}' not found.")
        sys.exit(1)

    # 1. Load existing data
    index_data = load_json_file(INDEX_FILE)
    sent_urls = load_sent_urls()
    
    with open(input_file, "r", encoding="utf-8") as f:
        jobs_list = json.load(f)

    generated_urls = []

    # 2. Process jobs
    for job in jobs_list:
        filename, job_entry = generate_job_page(job)
        generated_urls.append(job_entry["url"])
        
        # Update index if URL is new
        if not any(j["url"] == job_entry["url"] for j in index_data):
            index_data.append(job_entry)

    # 3. Save Index and Generated list
    save_json_file(INDEX_FILE, index_data)
    save_json_file(GENERATED_URLS_FILE, generated_urls)

    # 4. Handle Google Indexing and Tracking
    new_urls = [url for url in generated_urls if url not in sent_urls]
    
    if new_urls:
        print(f"Found {len(new_urls)} new URLs.")
        # Attempt to send to Google
        send_to_google_indexing(new_urls)
        
        # IMPORTANT: Even if API fails, we update the set so we track these as "processed"
        sent_urls.update(new_urls)
    else:
        print("No new URLs to process.")

    # 5. FORCE SAVE the sent_urls.json file
    save_sent_urls(sent_urls)
    print(f"Updated {SENT_URLS_FILE} with {len(sent_urls)} total tracked URLs.")

    # 6. Save pending text file
    with open(os.path.join(SCRIPT_DIR, "pending_urls.txt"), "w", encoding="utf-8") as f:
        for url in generated_urls:
            f.write(url + "\n")

if __name__ == "__main__":
    main()
