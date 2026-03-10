import os
import json
import requests
import datetime
import time
import re
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- CONFIG ---
SITE_URL = "https://global-job-hub.github.io/jobs/"
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
    
    # FORMAT: Standard Job Posting (As per Google Docs)
    html_template = f"""
<html>
  <head>
    <title>{job['title']}</title>
    <script type="application/ld+json">
    {{
      "@context" : "https://schema.org/",
      "@type" : "JobPosting",
      "title" : "{job['title']}",
      "description" : "{job['snippet']}",
      "identifier": {{
        "@type": "PropertyValue",
        "name": "{job['company']}",
        "value": "{job_id}"
      }},
      "datePosted" : "{datetime.date.today()}",
      "validThrough" : "{(datetime.date.today() + datetime.timedelta(days=60))}",
      "employmentType" : "FULL_TIME",
      "hiringOrganization" : {{
        "@type" : "Organization",
        "name" : "{job['company']}",
        "logo" : "https://global-job-hub.github.io/logo.png"
      }},
      "jobLocation": {{
        "@type": "Place",
        "address": {{
          "@type": "PostalAddress",
          "addressLocality": "{job['location']}",
          "addressCountry": "US"
        }}
      }}
    }}
    </script>
  </head>
  <body>
    <h1>{job['title']}</h1>
    <p>{job['snippet']}</p>
    <a href="{job['link']}">Apply for this Job</a>
  </body>
</html>
"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_template)
    return filename

def main():
    # 1. Fetch from Jooble (logic simplified for brevity)
    # ... (Add your Jooble fetch code here) ...
    
    # 2. Generate Pages
    new_urls = []
    for job in jobs[:20]: # Batch of 20
        fname = generate_job_page(job)
        new_urls.append(f"{SITE_URL}{fname}")

    # 3. CRITICAL: Commit and Push must happen here 
    # (The GitHub Action handles the push after the script ends)
    
    print("⏳ Waiting 90 seconds for GitHub Pages to deploy...")
    time.sleep(90) 

    # 4. Verify and Index
    info = json.loads(GOOGLE_CREDS)
    creds = service_account.Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/indexing"])
    service = build("indexing", "v3", credentials=creds)

    for url in new_urls:
        # Auto-check if URL is actually live
        check = requests.get(url)
        if check.status_code == 200:
            body = {"url": url, "type": "URL_UPDATED"}
            service.urlNotifications().publish(body=body).execute()
            print(f"✅ Live and Indexed: {url}")
        else:
            print(f"❌ Page not live yet ({check.status_code}). Skipping Indexing API.")

if __name__ == "__main__":
    main()
