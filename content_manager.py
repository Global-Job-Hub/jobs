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

# Professional Ad Slot Placeholder
AD_PLACEHOLDER = '<div class="ad-slot-placeholder" style="min-height:100px; background:#f9f9f9; display:flex; align-items:center; justify-content:center; border:1px dashed #ddd; font-size:12px; color:#aaa;">Advertisement</div>'

def slugify(text):
    text = str(text).lower()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[-\s]+', '-', text).strip('-')

def notify_google_removal(url):
    """Notifies Google Indexing API that a URL is deleted."""
    if not GOOGLE_CREDS:
        return
    try:
        info = json.loads(GOOGLE_CREDS)
        creds = service_account.Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/indexing"])
        service = build("indexing", "v3", credentials=creds)
        service.urlNotifications().publish(body={"url": url, "type": "URL_DELETED"}).execute()
        print(f"📡 Google Notified (DELETED): {url}")
    except Exception as e:
        print(f"⚠️ Google Notification Failed for {url}: {e}")

def cleanup_expired_jobs():
    """Scans local HTML files and deletes them if the validThrough date has passed."""
    print("🧹 Scanning for expired listings...")
    today = datetime.date.today().isoformat()
    files_deleted = 0

    for filename in os.listdir("."):
        if filename.endswith(".html") and "-" in filename:
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    content = f.read()
                
                match = re.search(r'"validThrough"\s*:\s*"(\d{4}-\d{2}-\d{2})', content)
                
                if match:
                    expiry_date = match.group(1)
                    if today > expiry_date:
                        print(f"❌ Expired: {filename} (Date was {expiry_date})")
                        job_url = f"{SITE_URL}{filename}"
                        notify_google_removal(job_url)
                        os.remove(filename)
                        files_deleted += 1
            except Exception as e:
                print(f"⚠️ Error processing {filename}: {e}")
    
    print(f"✅ Cleanup complete. {files_deleted} jobs removed.")

def generate_job_page(job):
    job_id = job.get('id', '0')
    title = job.get('title', 'Job Opening')
    company = job.get('company', 'Hiring Company')
    location = job.get('location', 'Remote')
    snippet = job.get('snippet', '').replace('"', "'")
    link = job.get('link', '#')
    
    updated_raw = job.get('updated', datetime.datetime.now().isoformat())
    post_date = updated_raw.split('T')[0] 
    
    if job.get('expire'):
        expiry_date = job.get('expire').split('T')[0]
    else:
        base_date = datetime.datetime.strptime(post_date, "%Y-%m-%d").date()
        expiry_date = (base_date + datetime.timedelta(days=30)).isoformat()
    
    title_slug = slugify(title)
    filename = f"{title_slug}-{job_id}.html"
    
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | {company} - Job Details</title>
    <script type="application/ld+json">
    {{
      "@context" : "https://schema.org/",
      "@type" : "JobPosting",
      "title" : "{title}",
      "description" : "{snippet}",
      "identifier": {{ "@type": "PropertyValue", "name": "{company}", "value": "{job_id}" }},
      "datePosted" : "{post_date}",
      "validThrough" : "{expiry_date}T00:00",
      "employmentType" : "FULL_TIME",
      "hiringOrganization" : {{ "@type" : "Organization", "name" : "{company}" }},
      "jobLocation": {{ "@type": "Place", "address": {{ "@type": "PostalAddress", "addressLocality": "{location}", "addressCountry": "US" }} }}
    }}
    </script>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f4f7f9; margin: 0; padding: 10px; color: #333; }}
        .wrapper {{ max-width: 850px; margin: 20px auto; background: #fff; border-radius: 12px; box-shadow: 0 5px 15px rgba(0,0,0,0.05); overflow: hidden; border: 1px solid #e1e4e8; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 18px 25px; text-align: left; border-bottom: 1px solid #f0f0f0; vertical-align: top; }}
        th {{ background: #f9f9f9; width: 35%; color: #666; font-size: 13px; text-transform: uppercase; letter-spacing: 1px; }}
        td {{ line-height: 1.6; font-size: 16px; }}
        .ad-row-container {{ padding: 10px; text-align: center; border-bottom: 1px solid #f0f0f0; background: #fff; }}
        .apply-btn {{ background: #28a745; color: #fff; padding: 15px 30px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block; transition: 0.3s; }}
        .apply-btn:hover {{ background: #218838; }}
    </style>
</head>
<body>
<div class="wrapper">
    <div class="ad-row-container">{AD_PLACEHOLDER}</div>
    <table>
        <tr><th>Job Title</th><td><strong style="color:#007bff; font-size:1.2em;">{title}</strong></td></tr>
        <tr><th>Company</th><td>{company}</td></tr>
        <tr><td colspan="2" class="ad-row-container">{AD_PLACEHOLDER}</td></tr>
        <tr><th>Description</th><td><div style="max-height:400px; overflow-y:auto;">{snippet}</div></td></tr>
        <tr><th>Location</th><td>{location}, US</td></tr>
        <tr><td colspan="2" class="ad-row-container">{AD_PLACEHOLDER}</td></tr>
        <tr><th>Post Date</th><td>{post_date}</td></tr>
        <tr><th>Valid Until</th><td>{expiry_date}</td></tr>
        <tr><td colspan="2" class="ad-row-container">{AD_PLACEHOLDER}</td></tr>
        <tr>
            <th>Action</th>
            <td><a href="{link}" class="apply-btn" target="_blank">Apply Now &raquo;</a></td>
        </tr>
    </table>
    <div class="ad-row-container">{AD_PLACEHOLDER}</div>
    <footer style="text-align:center; padding:25px; font-size:12px; color:#999; background:#fafafa;">
        <p>© 2026 Global Job Hub</p>
        <a href="{SITE_URL}">Back to Search</a> | 
        <a href="{SITE_URL}privacy-policy.html">Privacy Policy</a>
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
        print("🚀 Fetching jobs and building search index...")
        if not JOOBLE_KEY:
            print("❌ Error: JOOBLE_API_KEY missing.")
            return
            
        url = f"https://jooble.org/api/{JOOBLE_KEY}"
        res = requests.post(url, json={"keywords": "remote", "location": ""})
        jobs = res.json().get('jobs', [])
        
        new_urls = []
        all_jobs_data = [] # Data for the Search Bar
        
        for job in jobs[:20]:
            fname = generate_job_page(job)
            new_urls.append(f"{SITE_URL}{fname}")
            
            # Prepare data for fuzzy search index
            all_jobs_data.append({
                "t": job.get('title'),
                "c": job.get('company'),
                "l": job.get('location'),
                "u": fname  # The local filename for redirection
            })

        # Save the search index for index.html to use
        with open("jobs_index.json", "w", encoding="utf-8") as f:
            json.dump(all_jobs_data, f)
            
        # Save pending URLs for Google Indexing
        with open("pending_urls.txt", "w") as f:
            for u in new_urls: f.write(u + "\n")
            
        print(f"✅ {len(new_urls)} Job Pages and 'jobs_index.json' created.")

    elif mode == "--cleanup":
        cleanup_expired_jobs()

    elif mode == "--index":
        if not GOOGLE_CREDS:
            print("❌ Error: GOOGLE_CREDENTIALS missing.")
            return
        if not os.path.exists("pending_urls.txt"):
            print("ℹ️ No pending URLs.")
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
                        # Check if live before notifying Google
                        if requests.get(target).status_code == 200:
                            service.urlNotifications().publish(body={"url": target, "type": "URL_UPDATED"}).execute()
                            print(f"🚀 Indexed: {target}")
                        else:
                            print(f"⏳ Skipping {target} (Not live yet)")
                    except Exception as e:
                        print(f"❌ Error indexing {target}: {e}")
        except Exception as e:
            print(f"❌ Critical Auth Error: {e}")

if __name__ == "__main__":
    main()
