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
MAX_DAILY = 190

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[-\s]+', '-', text).strip('-')

def generate_job_page(job):
    job_id = job.get('id', '0')
    title_slug = slugify(job.get('title', 'job'))
    filename = f"{title_slug}-{job_id}.html"
    
    # Adsterra Codes from Secrets (or placeholders)
    banner_ad = os.environ.get("ADSTERRA_BANNER_CODE", '<div style="background:#eee; padding:20px;">Banner Ad Placeholder</div>')
    social_bar = os.environ.get("ADSTERRA_SOCIAL_BAR", "")

    # Official Footer Links
    footer_html = f"""
    <footer style="margin-top: 50px; padding: 20px; border-top: 1px solid #eee; text-align: center;">
        <div style="margin-bottom: 10px;">
            <a href="{SITE_URL}privacy-policy.html" style="margin: 0 10px; color: #666; text-decoration: none;">Privacy Policy</a> |
            <a href="{SITE_URL}terms-of-service.html" style="margin: 0 10px; color: #666; text-decoration: none;">Terms of Service</a> |
            <a href="{SITE_URL}contact.html" style="margin: 0 10px; color: #666; text-decoration: none;">Contact Us</a>
        </div>
        <p style="font-size: 0.8em; color: #999;">© 2026 Global Job Hub. All job data provided by Jooble API.</p>
    </footer>
    """

    # Full HTML with Schema and Ad-Wrapped Layout
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{job['title']} - {job['company']} | Global Job Hub</title>
    <style>
        body {{ font-family: 'Arial', sans-serif; background-color: #f4f4f4; margin: 0; padding: 10px; line-height: 1.6; }}
        .wrapper {{ max-width: 900px; margin: auto; }}
        .ad-slot {{ text-align: center; margin: 15px 0; overflow: hidden; }}
        .job-card {{ background: #fff; padding: 25px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #0056b3; font-size: 24px; }}
        .apply-button {{ display: block; background: #28a745; color: white; text-align: center; padding: 18px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 20px; margin: 20px 0; }}
        .description {{ font-size: 16px; color: #333; white-space: pre-wrap; }}
    </style>
    
    <script type="application/ld+json">
    {{
      "@context" : "https://schema.org/",
      "@type" : "JobPosting",
      "title" : "{job['title']}",
      "description" : "{job['snippet']}",
      "identifier": {{ "@type": "PropertyValue", "name": "{job['company']}", "value": "{job_id}" }},
      "datePosted" : "{datetime.date.today()}",
      "validThrough" : "{(datetime.date.today() + datetime.timedelta(days=60))}",
      "employmentType" : "FULL_TIME",
      "hiringOrganization" : {{ "@type" : "Organization", "name" : "{job['company']}", "logo" : "{SITE_URL}logo.png" }},
      "jobLocation": {{ "@type": "Place", "address": {{ "@type": "PostalAddress", "addressLocality": "{job['location']}", "addressCountry": "US" }} }}
    }}
    </script>
    {social_bar}
</head>
<body>
    <div class="wrapper">
        <div class="ad-slot">{banner_ad} </div>

        <div class="job-card">
            <h1>{job['title']}</h1>
            <p><strong>Company:</strong> {job['company']} | <strong>Location:</strong> {job['location']}</p>
            
            <div class="ad-slot">{banner_ad} </div>

            <div class="description">{job['snippet']}</div>

            <a href="{job['link']}" class="apply-button" target="_blank">Apply Now &raquo;</a>
        </div>

        <div class="ad-slot">{banner_ad} </div>
        {footer_html}
    </div>
</body>
</html>"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_template)
    return filename

def main():
    # Modes: --generate or --index
    mode = sys.argv[1] if len(sys.argv) > 1 else "--generate"

    if mode == "--generate":
        # 1. Fetch from Jooble
        url = f"https://jooble.org/api/{JOOBLE_KEY}"
        payload = {"keywords": "software engineer", "location": "Remote"}
        response = requests.post(url, json=payload)
        jobs = response.json().get('jobs', [])

        # 2. Generate and Store URLs
        new_urls = []
        for job in jobs[:20]:
            fname = generate_job_page(job)
            new_urls.append(f"{SITE_URL}{fname}")
        
        with open("pending_urls.txt", "w") as f:
            for u in new_urls: f.write(u + "\n")
        print(f"✅ Generated {len(new_urls)} pages.")

    elif mode == "--index":
        if not os.path.exists("pending_urls.txt"): return
        
        # 3. Notify Google
        info = json.loads(GOOGLE_CREDS)
        creds = service_account.Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/indexing"])
        service = build("indexing", "v3", credentials=creds)

        with open("pending_urls.txt", "r") as f:
            urls = f.readlines()

        for url in urls:
            url = url.strip()
            try:
                # Only ping Google if GitHub Pages has updated (Status 200)
                if requests.get(url).status_code == 200:
                    body = {"url": url, "type": "URL_UPDATED"}
                    service.urlNotifications().publish(body=body).execute()
                    print(f"🚀 Indexed: {url}")
            except Exception as e:
                print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
