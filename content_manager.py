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
    
    # Dates must be ISO 8601 (YYYY-MM-DD) for Google Indexing
    post_date = datetime.date.today().isoformat()
    expiry_date = (datetime.date.today() + datetime.timedelta(days=60)).isoformat()
    
    title_slug = slugify(title)
    filename = f"{title_slug}-{job_id}.html"
    
    # Adsterra Placeholder
    banner_ad = os.environ.get("ADSTERRA_BANNER_CODE", "")

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | {company} - Global Job Hub</title>
    
    <script type="application/ld+json">
    {{
      "@context" : "https://schema.org/",
      "@type" : "JobPosting",
      "title" : "{title}",
      "description" : "{snippet}",
      "identifier": {{
        "@type": "PropertyValue",
        "name": "{company}",
        "value": "{job_id}"
      }},
      "datePosted" : "{post_date}",
      "validThrough" : "{expiry_date}T00:00",
      "employmentType" : "FULL_TIME",
      "hiringOrganization" : {{
        "@type" : "Organization",
        "name" : "{company}",
        "sameAs" : "{SITE_URL}",
        "logo" : "{SITE_URL}logo.png"
      }},
      "jobLocation": {{
        "@type": "Place",
        "address": {{
          "@type": "PostalAddress",
          "addressLocality": "{location}",
          "addressCountry": "US"
        }}
      }},
      "baseSalary": {{
        "@type": "MonetaryAmount",
        "currency": "USD",
        "value": {{
          "@type": "QuantitativeValue",
          "value": 15.00,
          "unitText": "HOUR"
        }}
      }}
    }}
    </script>

    <style>
        body {{ font-family: 'Segoe UI', sans-serif; background: #f0f2f5; margin: 0; padding: 15px; }}
        .container {{ max-width: 800px; margin: auto; background: #fff; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); overflow: hidden; }}
        .header {{ background: #007bff; color: white; padding: 30px; text-align: center; }}
        .content {{ padding: 25px; line-height: 1.8; color: #333; }}
        .apply-btn {{ display: block; background: #28a745; color: white; text-align: center; padding: 20px; text-decoration: none; font-weight: bold; font-size: 1.2em; border-radius: 5px; margin: 20px 0; }}
        .ad-box {{ text-align: center; margin: 15px 0; min-height: 100px; overflow: hidden; }}
        footer {{ text-align: center; padding: 20px; font-size: 0.9em; color: #777; border-top: 1px solid #eee; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="ad-box">{banner_ad}</div>
        
        <div class="header">
            <h1 style="margin:0;">{title}</h1>
            <p style="margin:10px 0 0;">{company} • {location}</p>
        </div>

        <div class="content">
            <div class="ad-box">{banner_ad}</div>
            <div class="description">{snippet}</div>
            <a href="{link}" class="apply-btn" target="_blank">Apply for this Position &raquo;</a>
            <div class="ad-box">{banner_ad}</div>
        </div>

        <footer>
            <p>© 2026 Global Job Hub</p>
            <a href="{SITE_URL}privacy-policy.html">Privacy Policy</a> | 
            <a href="{SITE_URL}terms-of-service.html">Terms of Service</a> |
            <a href="{SITE_URL}contact.html">Contact Us</a>
        </footer>
    </div>
</body>
</html>"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_template)
    return filename

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--generate"

    if mode == "--generate":
        print("🚀 Fetching jobs from Jooble...")
        if not JOOBLE_KEY:
            print("❌ Error: JOOBLE_API_KEY is missing.")
            return
            
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
        if not GOOGLE_CREDS:
            print("❌ Error: GOOGLE_CREDENTIALS secret is empty.")
            return

        if not os.path.exists("pending_urls.txt"):
            print("ℹ️ No pending URLs to index.")
            return
        
        print("🔗 Notifying Google Indexing API...")
        try:
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
                        else:
                            print(f"⏳ Page {target} not live yet. Skipping.")
                    except Exception as e:
                        print(f"❌ Error indexing {target}: {e}")
        except Exception as e:
            print(f"❌ Critical Error: {e}")

if __name__ == "__main__":
    main()
