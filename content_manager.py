import os
import sys
import json
import requests
import datetime
import re
import hashlib

# --- CONFIG ---
SITE_URL = "https://global-job-hub.github.io/jobs/"
JOOBLE_KEY = os.environ.get("JOOBLE_API_KEY")

# Professional Ad Mapping
ADS = {
    "AD_728x90": os.environ.get("AD_728x90", ""),
    "AD_300x250": os.environ.get("AD_300x250", ""),
    "AD_468x60": os.environ.get("AD_468x60", ""),
    "AD_160x600": os.environ.get("AD_160x600", ""),
    "AD_160x300": os.environ.get("AD_160x300", ""),
    "AD_320x50": os.environ.get("AD_320x50", ""),
    "AD_NATIVE": os.environ.get("AD_NATIVE", "")
}

def get_ultra_sensitive_hash(job):
    """Serializes entire job to a hash. Any tiny change triggers an update."""
    job_string = json.dumps(job, sort_keys=True)
    return hashlib.sha256(job_string.encode('utf-8')).hexdigest()

def slugify(text):
    text = str(text).lower()
    return re.sub(r'[-\s]+', '-', re.sub(r'[^\w\s-]', '', text)).strip('-')

def cleanup_numeric_jobs():
    """Identifies job pages via the long Jooble ID and deletes if expired."""
    print("🧹 Starting Numeric-Based Job Cleanup...")
    today = datetime.date.today().isoformat()
    
    # Matches: - followed by 10+ digits .html (e.g., -3087854023968195667.html)
    job_pattern = re.compile(r"-(\d{10,})\.html$")

    for filename in os.listdir("."):
        if job_pattern.search(filename):
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Regex to find the hidden expiry tag
                match = re.search(r'', content)
                
                if match:
                    expiry_date = match.group(1)
                    if today > expiry_date:
                        print(f"🗑️ Expired: {filename} (Date: {expiry_date})")
                        os.remove(filename)
                    else:
                        print(f"✅ Active: {filename}")
                else:
                    print(f"⚠️ No Expiry Tag: {filename}. Removing for safety.")
                    os.remove(filename)
            except Exception as e:
                print(f"❌ Error processing {filename}: {e}")
    print("✅ Cleanup Complete.")

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

    # Expiry set to 30 days from now
    expiry_date = (datetime.date.today() + datetime.timedelta(days=30)).isoformat()
    post_date = datetime.date.today().isoformat()

    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()
            if f"DATA_HASH:{new_hash}" in content:
                return None # Skip if absolutely identical

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} at {company} | Job Details</title>
    <style>
        body {{ font-family: 'Inter', -apple-system, sans-serif; background: #f0f2f5; color: #1c1e21; margin: 0; }}
        .header-ad {{ background: #fff; padding: 15px; text-align: center; border-bottom: 1px solid #ddd; }}
        .layout {{ display: flex; max-width: 1250px; margin: 25px auto; gap: 20px; padding: 0 15px; }}
        .skyscraper {{ width: 160px; flex-shrink: 0; position: sticky; top: 20px; height: 600px; }}
        .main-card {{ flex-grow: 1; background: #fff; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #e1e4e8; overflow: hidden; }}
        .job-hero {{ padding: 35px; background: linear-gradient(to right, #ffffff, #f8f9fa); border-bottom: 1px solid #eee; }}
        .job-hero h1 {{ margin: 0; color: #007bff; font-size: 28px; letter-spacing: -0.5px; }}
        .meta-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; padding: 25px; background: #fafafa; border-bottom: 1px solid #eee; }}
        .meta-item {{ font-size: 14px; color: #555; }}
        .meta-label {{ font-weight: bold; text-transform: uppercase; font-size: 11px; color: #999; display: block; margin-bottom: 5px; }}
        .description-area {{ padding: 35px; line-height: 1.7; font-size: 16px; color: #333; }}
        .apply-section {{ padding: 40px; text-align: center; background: #fff; border-top: 1px solid #eee; }}
        .btn-apply {{ background: #28a745; color: #fff; padding: 20px 50px; text-decoration: none; border-radius: 10px; font-weight: bold; font-size: 20px; display: inline-block; box-shadow: 0 4px 14px rgba(40,167,69,0.3); }}
        .btn-apply:hover {{ background: #218838; transform: translateY(-2px); }}
        .footer-ad {{ position: fixed; bottom: 0; width: 100%; background: #fff; border-top: 1px solid #ddd; text-align: center; padding: 8px 0; z-index: 1000; }}
        @media (max-width: 1000px) {{ .skyscraper {{ display: none; }} .meta-grid {{ grid-template-columns: 1fr; }} }}
    </style>
</head>
<body>
    <div class="header-ad">{ADS['AD_728x90']}</div>
    <div class="layout">
        <aside class="skyscraper">{ADS['AD_160x600']}</aside>
        <main class="main-card">
            <div class="job-hero">
                <h1>{title}</h1>
                <p style="font-size: 19px; margin: 10px 0 0 0; color: #4b4f56;">{company}</p>
            </div>
            <div class="header-ad" style="border-top:none;">{ADS['AD_468x60']}</div>
            <div class="meta-grid">
                <div class="meta-item"><span class="meta-label">Location</span><strong>{location}</strong></div>
                <div class="meta-item"><span class="meta-label">Salary Estimate</span><strong>{salary}</strong></div>
                <div class="meta-item"><span class="meta-label">Posted Date</span>{post_date}</div>
                <div class="meta-item"><span class="meta-label">Work Type</span>Remote / Flexible</div>
            </div>
            <div class="header-ad">{ADS['AD_NATIVE']}</div>
            <div class="description-area">
                <h3 style="margin-top:0;">Job Overview</h3>
                {snippet}
            </div>
            <div class="header-ad">{ADS['AD_300x250']}</div>
            <div class="apply-section">
                <a href="{link}" class="btn-apply" target="_blank">Apply on Company Site &raquo;</a>
                <p style="margin-top:25px;"><a href="{SITE_URL}" style="color: #007bff; text-decoration: none; font-weight:600;">&larr; Back to Global Job Hub</a></p>
            </div>
        </main>
        <aside class="skyscraper">{ADS['AD_160x300']}</aside>
    </div>
    <div style="height: 80px;"></div>
    <div class="footer-ad">{ADS['AD_320x50']}</div>
</body>
</html>"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_template)
    return filename

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--generate"
    
    if mode == "--generate":
        print("🚀 Starting generation...")
        if not JOOBLE_KEY: return
        res = requests.post(f"https://jooble.org/api/{JOOBLE_KEY}", json={"keywords": "remote", "location": ""})
        jobs = res.json().get('jobs', [])
        
        for job in jobs[:20]:
            generate_job_page(job)
        print("✅ Generation complete.")

    elif mode == "--cleanup":
        cleanup_numeric_jobs()

if __name__ == "__main__":
    main()
