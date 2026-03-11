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

# ... (Keep your ADS dictionary and get_ultra_sensitive_hash from previous code) ...

def notify_google(url, action="URL_UPDATED"):
    """Notifies Google to Index or Remove a URL."""
    if not GOOGLE_CREDS:
        print(f"⚠️ Skipping Google Notification (No Creds): {url}")
        return
    try:
        info = json.loads(GOOGLE_CREDS)
        creds = service_account.Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/indexing"])
        service = build("indexing", "v3", credentials=creds)
        service.urlNotifications().publish(body={"url": url, "type": action}).execute()
        print(f"📡 Google Notified ({action}): {url}")
    except Exception as e:
        print(f"❌ Google Indexing Error: {e}")

def update_sitemap():
    """Generates a fresh sitemap.xml based on existing job files."""
    print("🗺️ Updating Sitemap...")
    job_pattern = re.compile(r"-(\d{10,})\.html$")
    urls = [SITE_URL] # Start with homepage
    
    for filename in os.listdir("."):
        if job_pattern.search(filename):
            urls.append(f"{SITE_URL}{filename}")
    
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url in urls:
        xml += f'  <url><loc>{url}</loc><changefreq>daily</changefreq></url>\n'
    xml += '</urlset>'
    
    with open("sitemap.xml", "w") as f:
        f.write(xml)
    print(f"✅ Sitemap updated with {len(urls)} links.")

def cleanup_numeric_jobs():
    """Finds expired jobs by date tag and deletes them."""
    print("🧹 Starting Numeric-Based Job Cleanup...")
    today = datetime.date.today().isoformat()
    job_pattern = re.compile(r"-(\d{10,})\.html$")
    deleted_count = 0

    for filename in os.listdir("."):
        if job_pattern.search(filename):
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    content = f.read()
                
                match = re.search(r'', content)
                if match:
                    expiry_date = match.group(1)
                    if today > expiry_date:
                        print(f"🗑️ Expired: {filename}")
                        notify_google(f"{SITE_URL}{filename}", action="URL_DELETED")
                        os.remove(filename)
                        deleted_count += 1
            except Exception as e:
                print(f"❌ Error: {e}")
    return deleted_count

# ... (Keep generate_job_page the same) ...

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--generate"
    
    if mode == "--generate":
        if not JOOBLE_KEY: return
        res = requests.post(f"https://jooble.org/api/{JOOBLE_KEY}", json={"keywords": "remote", "location": ""})
        jobs = res.json().get('jobs', [])
        
        # Track new URLs to index
        pending_file = "pending_urls.txt"
        with open(pending_file, "w") as f:
            for job in jobs[:20]:
                fname = generate_job_page(job)
                if fname:
                    f.write(f"{SITE_URL}{fname}\n")
        
    elif mode == "--index":
        if os.path.exists("pending_urls.txt"):
            with open("pending_urls.txt", "r") as f:
                urls = f.read().splitlines()
            for url in urls:
                notify_google(url, action="URL_UPDATED")
            update_sitemap()
            # Clear the file so we don't index the same ones twice
            os.remove("pending_urls.txt")

    elif mode == "--cleanup":
        count = cleanup_numeric_jobs()
        if count > 0:
            update_sitemap()

if __name__ == "__main__":
    main()
