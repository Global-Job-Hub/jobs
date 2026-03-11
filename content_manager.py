import os
import sys
import json
import re
import datetime
import requests  # <-- Missing this import

# --- CONFIG ---
SITE_URL = os.environ.get("SITE_URL", "https://global-job-hub.github.io/jobs/")
# Define JOOBLE_KEY here so all functions can see it
JOOBLE_KEY = os.environ.get("JOOBLE_API_KEY")

# Get Ads from Environment (GitHub Secrets)
ADS = {
    "AD_728X90": os.environ.get("AD_728X90", ""),
    "AD_300X250": os.environ.get("AD_300X250", ""),
    "AD_468X60": os.environ.get("AD_468X60", ""),
    "AD_160X600": os.environ.get("AD_160X600", ""),
    "AD_160X300": os.environ.get("AD_160X300", ""),
    "AD_320X50": os.environ.get("AD_320X50", ""),
    "AD_NATIVE": os.environ.get("AD_NATIVE", "")
}

def fetch_jobs():
    """Fetches jobs from Jooble and prints API health/quota info."""
    if not JOOBLE_KEY:
        print("❌ Error: JOOBLE_API_KEY is not set in environment.")
        return []

    url = f"https://api.jooble.org/api/{JOOBLE_KEY}"
    payload = {"keywords": "remote software developer", "location": ""}
    
    try:
        print("📡 Connecting to Jooble API...")
        response = requests.post(url, json=payload, timeout=15)
        
        # Log the quota headers
        remaining = response.headers.get('x-ratelimit-remaining', 'Not Found')
        print(f"📊 API Quota Status: {remaining}")
        
        if response.status_code == 200:
            data = response.json()
            jobs = data.get('jobs', [])
            print(f"✅ Success: Received {len(jobs)} jobs.")
            return jobs
        elif response.status_code == 429:
            print("🚨 ERROR 429: Quota Exceeded.")
            return []
        else:
            print(f"⚠️ API Status {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return []

def generate_job_page(job):
    """Skeleton for your job page generation logic."""
    # Add your specific job page generation code here
    pass

def generate_index():
    """Reads all current job files and updates index.html."""
    print("🏠 Updating Homepage (index.html)...")
    
    jobs_for_search = []
    job_pattern = re.compile(r".*-(\d{10,})\.html$")
    
    for filename in os.listdir("."):
        if job_pattern.search(filename):
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    content = f.read()
                    title_match = re.search(r"<title>(.*?) \| (.*?) \|", content)
                    if title_match:
                        jobs_for_search.append({
                            "t": title_match.group(1).strip(),
                            "c": title_match.group(2).strip(),
                            "l": "Remote",
                            "u": filename
                        })
            except Exception as e:
                print(f"⚠️ Error reading {filename}: {e}")

    with open("jobs_index.json", "w", encoding="utf-8") as f:
        json.dump(jobs_for_search, f)

    # Use a raw string or double braces for CSS/JS to avoid f-string conflicts
    index_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="monetag" content="d870a49cae4858d7d66e3744953ea5af">
    <title>Global Job Hub | Find Your Next Career</title>
    <script src="https://cdn.jsdelivr.net/npm/fuse.js@6.6.2"></script>
    <style>
        :root {{ --primary: #007bff; --bg: #f4f7f9; --text: #333; }}
        body {{ font-family: 'Segoe UI', Roboto, Helvetica, sans-serif; text-align: center; background-color: var(--bg); margin: 0; color: var(--text); display: flex; flex-direction: column; align-items: center; }}
        .ad-center {{ margin: 15px auto; display: flex; flex-direction: column; align-items: center; justify-content: center; }}
        .ad-label {{ display: block; font-size: 10px; color: #bbb; text-transform: uppercase; margin-bottom: 5px; }}
        .main-layout {{ display: flex; justify-content: center; gap: 20px; width: 100%; max-width: 1300px; margin: 20px auto; }}
        .container {{ background: white; padding: 40px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); width: 100%; max-width: 600px; }}
        .skyscraper {{ width: 160px; min-height: 600px; background: #fff; border: 1px solid #e1e4e8; display: none; position: sticky; top: 10px; }}
        @media (min-width: 1000px) {{ .skyscraper {{ display: block; }} }}
        .search-container {{ position: relative; width: 100%; margin-top: 25px; }}
        #jobSearch {{ width: 100%; padding: 18px 25px; border-radius: 12px; border: 2px solid #eee; }}
        #results {{ position: absolute; top: 100%; left: 0; right: 0; background: #fff; border: 1px solid #ddd; display: none; z-index: 1000; text-align: left; }}
        .result-item {{ padding: 15px 20px; cursor: pointer; border-bottom: 1px solid #f8f8f8; }}
        .footer-links {{ display: flex; justify-content: center; gap: 12px; margin-bottom: 20px; }}
        .footer-btn {{ font-size: 13px; color: #555; text-decoration: none; padding: 10px 18px; border: 1px solid #e1e4e8; border-radius: 25px; }}
        .sticky-footer {{ position: fixed; bottom: 0; left: 0; width: 100%; background: white; border-top: 1px solid #ddd; z-index: 9999; padding: 8px 0; }}
    </style>
</head>
<body>
    <div class="ad-center">
        <span class="ad-label">Advertisement</span>
        {ADS['AD_728X90']}
    </div>
    <div class="main-layout">
        <div class="skyscraper">
            <span class="ad-label">Sponsored</span>
            {ADS['AD_160X600']}
        </div>
        <div class="container">
            <h1>🌐 Global Job Hub</h1>
            <p>Connecting you to millions of opportunities worldwide.</p>
            <div class="ad-center">{ADS['AD_468X60']}</div>
            <div class="search-container">
                <input type="text" id="jobSearch" placeholder="Search..." autocomplete="off">
                <div id="results"></div>
            </div>
            <div class="ad-center">{ADS['AD_NATIVE']}</div>
            <div class="ad-center" style="margin-top:30px;">
                <span class="ad-label">Specially Recommended</span>
                {ADS['AD_300X250']}
            </div>
            <footer style="margin-top:40px; border-top:1px solid #eee; padding-top:20px;">
                <div class="footer-links">
                    <a href="privacy-policy.html" class="footer-btn">🛡️ Privacy Policy</a>
                    <a href="terms-of-service.html" class="footer-btn">⚖️ Terms of Service</a>
                    <a href="mailto:support@globaljobhub.com" class="footer-btn">✉️ Contact Us</a>
                </div>
                <div style="font-size:12px; color:#bbb;">© 2026 Global Job Hub</div>
            </footer>
        </div>
        <div class="skyscraper">
            <span class="ad-label">Sponsored</span>
            {ADS['AD_160X300']}
        </div>
    </div>
    <div class="sticky-footer">
        <div class="ad-center" style="margin:0;">{ADS['AD_320X50']}</div>
    </div>
    <script>
        const input = document.getElementById('jobSearch');
        const results = document.getElementById('results');
        let fuse;
        fetch('jobs_index.json').then(res => res.json()).then(data => {{
            fuse = new Fuse(data, {{ keys: ['t', 'c', 'l'], threshold: 0.3 }});
        }});
        input.addEventListener('input', () => {{
            const val = input.value.trim();
            results.innerHTML = '';
            if (!fuse || val.length < 2) {{ results.style.display = 'none'; return; }}
            const searchResult = fuse.search(val).slice(0, 10);
            if (searchResult.length > 0) {{
                results.style.display = 'block';
                searchResult.forEach(match => {{
                    const job = match.item;
                    const div = document.createElement('div');
                    div.className = 'result-item';
                    div.innerHTML = `<strong>${{job.t}}</strong><br><small>${{job.c}} • ${{job.l}}</small>`;
                    div.onmousedown = () => window.location.href = job.u;
                    results.appendChild(div);
                }});
            }}
        }});
        input.addEventListener('blur', () => setTimeout(() => results.style.display = 'none', 200));
    </script>
</body>
</html>"""
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(index_template)
    print(f"✅ index.html and jobs_index.json updated.")

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--generate"
    
    if mode == "--generate":
        jobs_list = fetch_jobs()
        if jobs_list:
            for job in jobs_list[:20]:
                generate_job_page(job)
        generate_index()
    elif mode == "--index":
        generate_index()
    else:
        print("Usage: python content_manager.py [--generate | --index]")

if __name__ == "__main__":
    main()
