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

# Fetch Ad Secrets - These will be injected into the HTML template
ADS = {
    "AD_728x90": os.environ.get("AD_728x90", ""),
    "AD_300x250": os.environ.get("AD_300x250", ""),
    "AD_468x60": os.environ.get("AD_468x60", ""),
    "AD_160x600": os.environ.get("AD_160x600", ""),
    "AD_160x300": os.environ.get("AD_160x300", ""),
    "AD_320x50": os.environ.get("AD_320x50", ""),
    "AD_NATIVE": os.environ.get("AD_NATIVE", "")
}

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

    # UNIQUE CHECK: Don't recreate if it exists
    if os.path.exists(filename):
        return None 

    post_date = datetime.date.today().isoformat()
    expiry_date = (datetime.date.today() + datetime.timedelta(days=30)).isoformat()
    
    # PROFESSIONAL LAYOUT TEMPLATE
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | Global Job Hub</title>
    <style>
        :root {{ --primary: #007bff; --bg: #f8f9fa; --text: #333; }}
        body {{ font-family: 'Inter', system-ui, sans-serif; background: var(--bg); margin: 0; color: var(--text); line-height: 1.5; }}
        
        /* Ad Containers */
        .ad-top {{ text-align: center; padding: 20px 0; background: #fff; border-bottom: 1px solid #eee; }}
        .ad-inline {{ margin: 20px 0; text-align: center; }}
        .sticky-footer-ad {{ position: fixed; bottom: 0; left: 0; width: 100%; background: #fff; border-top: 1px solid #ddd; z-index: 999; text-align: center; padding: 5px 0; }}

        /* Main Layout */
        .container {{ display: flex; max-width: 1200px; margin: 0 auto; padding: 20px; gap: 20px; }}
        .sidebar {{ width: 160px; flex-shrink: 0; }}
        .main-content {{ flex-grow: 1; background: #fff; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); overflow: hidden; border: 1px solid #eef0f2; }}
        
        /* Job Table */
        .job-header {{ background: #fff; padding: 30px; border-bottom: 1px solid #eee; }}
        .job-header h1 {{ margin: 0; color: var(--primary); font-size: 24px; }}
        .job-table {{ width: 100%; border-collapse: collapse; }}
        .job-table th {{ text-align: left; padding: 15px 25px; background: #fafafa; color: #666; font-size: 13px; text-transform: uppercase; width: 25%; }}
        .job-table td {{ padding: 15px 25px; border-bottom: 1px solid #f6f6f6; }}
        
        .apply-area {{ padding: 30px; text-align: center; background: #fcfcfc; }}
        .btn-apply {{ background: #28a745; color: white; padding: 16px 40px; text-decoration: none; border-radius: 50px; font-weight: bold; display: inline-block; font-size: 18px; }}
        
        .footer-nav {{ background: #eef6ff; padding: 30px; text-align: center; margin-top: 20px; }}
        .btn-more {{ color: var(--primary); text-decoration: none; font-weight: 600; border: 2px solid var(--primary); padding: 10px 25px; border-radius: 25px; }}

        @media (max-width: 1000px) {{ .sidebar {{ display: none; }} .container {{ padding: 10px; }} }}
    </style>
</head>
<body>

    <div class="ad-top">{ADS['AD_728x90']}</div>

    <div class="container">
        <aside class="sidebar">{ADS['AD_160x600']}</aside>

        <main class="main-content">
            <div class="job-header">
                <h1>{title}</h1>
                <p style="color: #666;">{company} • {location}</p>
            </div>

            <div class="ad-inline">{ADS['AD_468x60']}</div>

            <table class="job-table">
                <tr><th>Description</th><td>{snippet}</td></tr>
                <tr><td colspan="2"><div class="ad-inline">{ADS['AD_NATIVE']}</div></td></tr>
                <tr><th>Location</th><td>{location}, United States</td></tr>
                <tr><th>Posted</th><td>{post_date}</td></tr>
                <tr><th>Expiry</th><td>{expiry_date}</td></tr>
            </table>

            <div class="ad-inline">{ADS['AD_300x250']}</div>

            <div class="apply-area">
                <a href="{link}" class="btn-apply" target="_blank">Apply for this Position &rarr;</a>
            </div>

            <div class="footer-nav">
                <p>Not what you're looking for?</p>
                <a href="{SITE_URL}" class="btn-more">Explore More Remote Jobs</a>
            </div>
        </main>

        <aside class="sidebar">{ADS['AD_160x300']}</aside>
    </div>

    <div style="height: 80px;"></div> <div class="sticky-footer-ad">{ADS['AD_320x50']}</div>

</body>
</html>"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_template)
    return filename

# ... (rest of the main function remains the same as your provided code) ...
