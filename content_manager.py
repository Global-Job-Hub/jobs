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
LOG_FILE = "indexing_tracker.json"

def slugify(text):
    text = str(text).lower()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[-\s]+', '-', text).strip('-')

def generate_job_page(job):
    job_id = job.get('id', '0')
    title = job.get('title', 'Job Opening')
    company = job.get('company', 'Hiring Company')
    location = job.get('location', 'Remote')
    snippet = job.get('snippet', '').replace('"', "'")
    link = job.get('link', '#')
    
    title_slug = slugify(title)
    filename = f"{title_slug}-{job_id}.html"
    
    banner_ad = os.environ.get("ADSTERRA_BANNER_CODE", "")

    # The Job Content Template
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - {company}</title>
    <script type="application/ld+json">
    {{
      "@context" : "https://schema.org/",
      "@type" : "JobPosting",
      "title" : "{title}",
      "description" : "{snippet}",
      "identifier": {{ "@type": "PropertyValue", "name": "{company}", "value": "{job_id}" }},
      "datePosted" : "{datetime.date.today()}",
      "hiringOrganization" : {{ "@type" : "Organization", "name" : "{company}" }},
      "jobLocation": {{ "@type": "Place", "address": {{ "@type": "PostalAddress", "addressLocality": "{location}", "addressCountry": "US" }} }}
    }}
    </script>
    <style>
        body {{ font-family: sans-serif; background: #f4f4f4; padding: 20px; }}
        .card {{ background: white; padding: 20px; max-width: 700px; margin: auto; border-radius: 10px; }}
        .btn {{ display: block; background: #28a745; color: white; text-align: center; padding: 15px; text-decoration: none; font-weight: bold; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="card">
        <div style="text-align:center;">{banner_ad}</div>
        <h1>{title}</h1>
        <p><strong>{company}</strong> | {location}</p>
        <div>{snippet}</div>
        <a href="{link}" class="btn">Apply Now</a>
        <div style="text-align:center; margin-top:20px;">{banner_ad}</div>
        <footer style="text-align:center; margin-top:30px; font-size:12px;">
            <a href="{SITE_URL}privacy-policy.html">Privacy Policy</a> | 
            <a href="{SITE_URL}terms-of-service.html">Terms of Service</a>
        </footer>
    </div>
</body>
</html>"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_template)
    return filename

def main():
    # Set default mode if none provided
    mode = sys.argv[1] if len(sys.argv) > 1 else "--generate"

    if mode == "--generate":
        print("🚀 Fetching jobs from Jooble...")
        url = f"https://jooble.org/api/{JOOBLE_KEY}"
        res = requests.post(url, json={"keywords": "remote", "location": ""})
        jobs = res.json().get('jobs', [])

        new_urls = []
        for job in jobs[:20]:
            fname = generate_job_page(job)
            new_urls.append(f"{SITE_URL}{fname}")
        
        with open("pending_urls.txt", "w") as f:
            for u in new_urls: f.write(u + "\n")
        print(f"✅ Created {len(new_urls)} jobs.")

    elif mode == "--index":
        if not os.path.exists("pending_urls.txt"):
            print("ℹ️ No pending URLs to index.")
            return
        
        print("🔗 Notifying Google Indexing API...")
        info = json.loads(GOOGLE_CREDS)
        creds = service_account.Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/indexing"])
        service = build("indexing", "v3", credentials=creds)

        with open("pending_urls.txt", "r") as f:
            for url in f:
                target = url.strip()
                try:
                    # Quick check if live
                    if requests.get(target).status_code == 200:
                        service.urlNotifications().publish(body={"url": target, "type": "URL_UPDATED"}).execute()
                        print(f"🚀 Indexed: {target}")
                except Exception as e:
                    print(f"❌ Error indexing {target}: {e}")

if __name__ == "__main__":
    main()
