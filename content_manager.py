import os
import sys
import json
import requests
import datetime
import re
import hashlib
import random

# --- CONFIG ---
SITE_URL = "https://global-job-hub.github.io/jobs/"
JOOBLE_KEY = os.environ.get("JOOBLE_API_KEY")

ADS = {
    "AD_728X90": os.environ.get("AD_728X90", ""),
    "AD_300X250": os.environ.get("AD_300X250", ""),
    "AD_468X60": os.environ.get("AD_468X60", ""),
    "AD_160X600": os.environ.get("AD_160X600", ""),
    "AD_160X300": os.environ.get("AD_160X300", ""),
    "AD_320X50": os.environ.get("AD_320X50", ""),
    "AD_NATIVE": os.environ.get("AD_NATIVE", "")
}

def get_related_jobs(current_filename):
    """Scans the directory for other HTML job files to create a recommendation grid."""
    job_files = [f for f in os.listdir(".") if f.endswith(".html") and "-" in f and f != current_filename]
    random.shuffle(job_files)
    selected = job_files[:4]
    
    html_grid = '<div class="related-grid">'
    for f in selected:
        # Create a clean title from the filename (e.g., "software-engineer-123.html" -> "Software Engineer")
        display_name = f.split("-")[:-1]
        display_name = " ".join(display_name).title()
        html_grid += f'<a href="{SITE_URL}{f}" class="related-card">{display_name}</a>'
    html_grid += '</div>'
    return html_grid

def generate_job_page(job):
    job_id = job.get('id', '0')
    title = job.get('title', 'Job Opening')
    company = job.get('company', 'Hiring Company')
    location = job.get('location', 'Remote')
    salary = job.get('salary', 'Competitive')
    snippet = job.get('snippet', '').replace('"', "'")
    link = job.get('link', '#')
    
    new_hash = get_ultra_sensitive_hash(job)
    filename = f"{slugify(title)}-{job_id}.html"
    expiry_date = (datetime.date.today() + datetime.timedelta(days=30)).isoformat()
    
    # Generate the Related Jobs HTML
    related_jobs_html = get_related_jobs(filename)

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | {company} | Global Job Hub</title>
    <style>
        body {{ font-family: 'Inter', sans-serif; background: #f4f7f9; color: #333; margin: 0; padding-bottom: 80px; }}
        .ad-row {{ text-align: center; padding: 15px; background: #fff; border-bottom: 1px solid #eee; }}
        .layout {{ display: flex; max-width: 1300px; margin: 20px auto; gap: 20px; padding: 0 15px; }}
        .sidebar {{ width: 160px; flex-shrink: 0; position: sticky; top: 10px; height: fit-content; }}
        .main-content {{ flex-grow: 1; background: #fff; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); overflow: hidden; }}
        .meta-info {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; padding: 20px; background: #fafafa; border-top: 1px solid #eee; border-bottom: 1px solid #eee; }}
        .description {{ padding: 30px; line-height: 1.8; min-height: 300px; }}
        .apply-area {{ text-align: center; padding: 40px; background: #fcfcfc; }}
        .btn {{ background: #28a745; color: #fff; padding: 18px 45px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block; font-size: 18px; }}
        
        /* RELATED JOBS STYLING */
        .related-section {{ padding: 30px; background: #fff; border-top: 1px solid #eee; }}
        .related-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 15px; }}
        .related-card {{ padding: 15px; border: 1px solid #e1e4e8; border-radius: 8px; text-decoration: none; color: #007bff; font-weight: 500; font-size: 14px; transition: 0.2s; }}
        .related-card:hover {{ background: #f0f7ff; border-color: #007bff; }}
        
        .sticky-footer {{ position: fixed; bottom: 0; width: 100%; background: #fff; text-align: center; border-top: 1px solid #ddd; padding: 5px 0; z-index: 1000; }}
        @media (max-width: 1100px) {{ .sidebar {{ display: none; }} .related-grid {{ grid-template-columns: 1fr; }} }}
    </style>
</head>
<body>
    <div class="ad-row">{ADS['AD_728X90']}</div>
    <div class="layout">
        <aside class="sidebar">{ADS['AD_160X600']}</aside>
        <main class="main-content">
            <div style="padding:30px;">
                <h1 style="color:#007bff; margin:0;">{title}</h1>
                <p style="font-size:18px; color:#666; margin-top:5px;">{company} • {location}</p>
            </div>
            <div class="ad-row" style="border:none;">{ADS['AD_468X60']}</div>
            <div class="meta-info">
                <div><strong>📍 Location:</strong> {location}</div>
                <div><strong>💰 Salary:</strong> {salary}</div>
            </div>
            <div style="padding:20px; text-align:center;">{ADS['AD_NATIVE']}</div>
            <div class="description">{snippet}</div>
            <div class="ad-row" style="border:none; padding:20px;">{ADS['AD_300X250']}</div>
            <div class="apply-area">
                <a href="{link}" class="btn" target="_blank">Apply Now &raquo;</a>
            </div>

            <div class="related-section">
                <h3 style="margin:0;">Featured Remote Opportunities</h3>
                {related_jobs_html}
            </div>
        </main>
        <aside class="sidebar">{ADS['AD_160X300']}</aside>
    </div>
    <div class="sticky-footer">{ADS['AD_320X50']}</div>
</body>
</html>"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_template)
    return filename
