import os
import json
import requests
import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- CONFIGURATION ---
JOOBLE_KEY = os.environ.get("JOOBLE_API_KEY")
SITE_URL = "https://global-job-hub.github.io/jobs/"
GOOGLE_CREDS = os.environ.get("GOOGLE_CREDENTIALS")

# --- 1. FETCH JOBS FROM JOOBLE ---
def fetch_jooble_jobs():
    url = f"https://jooble.org/api/{JOOBLE_KEY}"
    # Change keywords/location to target specific jobs
    payload = {"keywords": "software engineer", "location": "Remote"}
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json().get('jobs', [])
    print("❌ Jooble API Error")
    return []

# --- 2. GENERATE HTML PAGE ---
def generate_job_page(job):
    # Create a unique filename/slug
    job_id = job.get('id', '0')
    slug = job.get('title').lower().replace(" ", "-").replace("/", "-")
    filename = f"{slug}-{job_id}.html"
    
    # Adsterra Placeholder (Add your actual codes in GitHub Secrets)
    ad_banner = os.environ.get("ADSTERRA_BANNER_CODE", "")
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{job['title']} - Global Job Hub</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ font-family: sans-serif; line-height: 1.6; padding: 20px; max-width: 800px; margin: auto; }}
        .apply-btn {{ display: inline-block; padding: 15px 25px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; }}
        .ad-space {{ margin: 20px 0; border: 1px solid #ddd; padding: 10px; text-align: center; }}
    </style>
    
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
    <h3>Company: {job['company']} | Location: {job['location']}</h3>
    
    <div class="ad-space">{ad_banner}</div>

    <div class="description">
        {job['snippet']}
    </div>

    <div style="margin-top: 30px;">
        <a href="{job['link']}" class="apply-btn">View full job on Jooble</a>
    </div>

    <p><small>Powered by Jooble API</small></p>
</body>
</html>
"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    return filename

# --- 3. NOTIFY GOOGLE INDEXING API ---
def notify_google(page_url):
    try:
        info = json.loads(GOOGLE_CREDS)
        creds = service_account.Credentials.from_service_account_info(
            info, scopes=["https://www.googleapis.com/auth/indexing"]
        )
        service = build("indexing", "v3", credentials=creds)
        body = {"url": page_url, "type": "URL_UPDATED"}
        service.urlNotifications().publish(body=body).execute()
        print(f"✅ Indexed: {page_url}")
    except Exception as e:
        print(f"❌ Indexing Failed for {page_url}: {e}")

# --- MAIN EXECUTION ---
def main():
    jobs = fetch_jooble_jobs()
    print(f"Fetched {len(jobs)} jobs.")
    
    for job in jobs[:10]: # Start with 10 to test
        filename = generate_job_page(job)
        full_url = f"{SITE_URL}{filename}"
        notify_google(full_url)

if __name__ == "__main__":
    main()
