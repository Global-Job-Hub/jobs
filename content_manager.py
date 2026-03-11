import os
import sys
import json
import re
import time
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- CONFIG ---
SITE_URL = "https://global-job-hub.github.io/jobs/"
SENT_URLS_FILE = "sent_urls.json"  # store URLs already sent to Google
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "service_account.json")

# --- Load ad units from GitHub Secrets (or fallback placeholders) ---
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

def load_sent_urls():
    if os.path.exists(SENT_URLS_FILE):
        with open(SENT_URLS_FILE, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    return set()

def save_sent_urls(urls):
    with open(SENT_URLS_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(urls), f, indent=2)

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
    
    ad_top = AD_728X90
    ad_middle = AD_300X250
    ad_sidebar = AD_160X600
    ad_bottom = AD_468X60
    ad_inline = AD_NATIVE
    
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | {company} - Job Details</title>
<script type="application/ld+json">
{{
  "@context": "https://schema.org/",
  "@type": "JobPosting",
  "title": "{title}",
  "description": "{description}",
  "identifier": {{
    "@type": "PropertyValue",
    "name": "{company}",
    "value": "{job_id}"
  }},
  "datePosted": "{post_date}",
  "validThrough": "{valid_through}T23:59",
  "employmentType": "{job.get('employment_type', 'FULL_TIME')}",
  "hiringOrganization": {{
    "@type": "Organization",
    "name": "{company}",
    "sameAs": "{SITE_URL}"
  }},
  "jobLocation": {{
    "@type": "Place",
    "address": {{
      "@type": "PostalAddress",
      "addressLocality": "{city}",
      "addressCountry": "{country}"
    }}
  }}
}}
</script>
<style>
body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; margin: 0; padding: 20px; color: #333; }}
.main-container {{ max-width: 900px; margin: 0 auto; background: #fff; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); overflow: hidden; }}
.header {{ background: #007bff; color: white; padding: 30px; text-align: center; }}
.content-table {{ width: 100%; border-collapse: collapse; }}
.content-table th, .content-table td {{ padding: 20px; text-align: left; border-bottom: 1px solid #eee; vertical-align: top; }}
.content-table th {{ background: #fafafa; width: 30%; color: #666; font-weight: 600; }}
.description-box {{ max-height: 500px; overflow-y: auto; line-height: 1.8; }}
.ad-section {{ padding: 15px; text-align: center; background: #fff; border-bottom: 1px solid #eee; }}
.apply-container {{ padding: 40px; text-align: center; }}
.apply-btn {{ background: #28a745; color: white; padding: 18px 35px; text-decoration: none; border-radius: 5px; font-size: 18px; font-weight: bold; transition: background 0.2s; display: inline-block; }}
.apply-btn:hover {{ background: #218838; }}
footer {{ background: #343a40; color: #ccc; padding: 20px; text-align: center; font-size: 14px; }}
footer a {{ color: #fff; text-decoration: none; margin: 0 10px; }}
</style>
</head>
<body>

<div class="main-container">
    <div class="header">
        <h1 style="margin:0;">{title}</h1>
        <p style="margin:10px 0 0;">{company} • {location_str}</p>
    </div>

    <div class="ad-section">{ad_top}</div>

    <table class="content-table">
        <tr>
            <th>Company</th>
            <td><strong>{company}</strong></td>
        </tr>
        <tr>
            <th>Job Location</th>
            <td>{location_str}</td>
        </tr>
        <tr><td colspan="2" class="ad-section">{ad_sidebar}</td></tr>
        <tr>
            <th>Job Description</th>
            <td><div class="description-box">{description}<br><div class="ad-section">{ad_inline}</div></div></td>
        </tr>
        <tr>
            <th>Employment Type</th>
            <td>{job.get('employment_type', 'Full-Time')}</td>
        </tr>
        <tr><td colspan="2" class="ad-section">{ad_middle}</td></tr>
        <tr>
            <th>Posted On</th>
            <td>{post_date}</td>
        </tr>
        <tr>
            <th>Closing Date</th>
            <td>{valid_through}</td>
        </tr>
        <tr><td colspan="2" class="ad-section">{ad_bottom}</td></tr>
    </table>

    <div class="apply-container">
        <p>Interested in this position? Click below to apply.</p>
        <a href="{apply_url}" class="apply-btn" target="_blank">Apply Now &raquo;</a>
    </div>

    <footer>
        <p>© 2026 Global Job Hub. All rights reserved.</p>
        <p>
            <a href="{SITE_URL}">Home</a> | 
            <a href="{SITE_URL}privacy.html">Privacy Policy</a> | 
            <a href="{SITE_URL}contact.html">Contact</a>
        </p>
    </footer>
</div>

</body>
</html>"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_template)
    
    return filename

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
            service.urlNotifications().publish(
                body={"url": url, "type": "URL_UPDATED"}
            ).execute()
            print(f"Sent URL to Google Indexing API: {url}")
            sent.add(url)
            time.sleep(1)  # avoid spamming API too quickly
        except Exception as e:
            print(f"Failed to send {url}: {e}")
    return sent

def main():
    if len(sys.argv) < 2:
        print("Usage: python content_manager.py jobs.json")
        sys.exit(1)

    input_file = sys.argv[1]
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)

    print(f"Loading jobs from {input_file}...")
    with open(input_file, "r", encoding="utf-8") as f:
        jobs_list = json.load(f)

    generated_urls = []
    for job in jobs_list:
        try:
            filename = generate_job_page(job)
            full_url = f"{SITE_URL}{filename}"
            generated_urls.append(full_url)
            print(f"Created: {filename}")
        except Exception as e:
            print(f"Failed to process job {job.get('id')}: {e}")

    # Load already sent URLs
    sent_urls = load_sent_urls()
    new_urls = [url for url in generated_urls if url not in sent_urls]

    if new_urls:
        print(f"Sending {len(new_urls)} new URLs to Google Indexing API...")
        sent_now = send_to_google_indexing(new_urls)
        sent_urls.update(sent_now)
        save_sent_urls(sent_urls)
    else:
        print("No new URLs to send. All URLs already sent previously.")

    # Save pending URLs (optional)
    with open("pending_urls.txt", "w", encoding="utf-8") as f:
        for url in generated_urls:
            f.write(url + "\n")

    print(f"Finished. {len(generated_urls)} job pages generated. {len(new_urls)} new URLs sent to Google.")

if __name__ == "__main__":
    main()
