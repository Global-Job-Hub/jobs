import os
import sys
import json
import re
import datetime

# --- CONFIG ---
SITE_URL = os.environ.get("SITE_URL", "https://global-job-hub.github.io/jobs/")

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

def generate_index():
    """Reads all current job files and updates index.html with the latest ads and search data."""
    print("🏠 Updating Homepage (index.html)...")
    
    jobs_for_search = []
    # Matches files like: software-engineer-1234567890.html
    job_pattern = re.compile(r".*-(\d{10,})\.html$")
    
    for filename in os.listdir("."):
        if job_pattern.search(filename):
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    content = f.read()
                    # Extracts Title and Company
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

    # Write the JSON search index for Fuse.js
    with open("jobs_index.json", "w", encoding="utf-8") as f:
        json.dump(jobs_for_search, f)

    # The full index.html Template
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
        .ad-center {{ margin: 15px auto; display: flex; flex-direction: column; align-items: center; justify-content: center; overflow: hidden; }}
        .ad-label {{ display: block; font-size: 10px; color: #bbb; text-transform: uppercase; margin-bottom: 5px; width: 100%; }}
        .main-layout {{ display: flex; justify-content: center; align-items: flex-start; gap: 20px; width: 100%; max-width: 1300px; margin: 20px auto; padding: 0 15px; box-sizing: border-box; }}
        .container {{ background: white; padding: 40px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); width: 100%; max-width: 600px; border: 1px solid #e1e4e8; position: relative; z-index: 2; }}
        .skyscraper {{ width: 160px; min-height: 600px; background: #fff; border: 1px solid #e1e4e8; border-radius: 8px; display: none; overflow: hidden; position: sticky; top: 10px; }}
        @media (min-width: 1000px) {{ .skyscraper {{ display: block; }} }}
        h1 {{ color: var(--primary); margin-bottom: 10px; font-size: 2.5rem; letter-spacing: -1px; }}
        .search-container {{ position: relative; width: 100%; margin-top: 25px; }}
        #jobSearch {{ width: 100%; padding: 18px 25px; border-radius: 12px; border: 2px solid #eee; font-size: 17px; outline: none; transition: 0.3s; box-shadow: 0 4px 6px rgba(0,0,0,0.02); }}
        #jobSearch:focus {{ border-color: var(--primary); box-shadow: 0 4px 12px rgba(0,123,255,0.1); }}
        #results {{ position: absolute; top: 100%; left: 0; right: 0; background: #fff; border-radius: 0 0 12px 12px; border: 1px solid #ddd; display: none; z-index: 1000; text-align: left; max-height: 400px; overflow-y: auto; box-shadow: 0 10px 20px rgba(0,0,0,0.1); }}
        .result-item {{ padding: 15px 20px; cursor: pointer; border-bottom: 1px solid #f8f8f8; transition: 0.2s; }}
        .result-item:hover {{ background: #f0f7ff; padding-left: 25px; color: var(--primary); }}
        .footer-links {{ display: flex; justify-content: center; gap: 12px; flex-wrap: wrap; margin-bottom: 20px; }}
        .footer-btn {{ font-size: 13px; color: #555; text-decoration: none; padding: 10px 18px; border: 1px solid #e1e4e8; border-radius: 25px; background: #fff; transition: 0.2s; }}
        .footer-btn:hover {{ border-color: var(--primary); color: var(--primary); transform: translateY(-2px); }}
        .sticky-footer {{ position: fixed; bottom: 0; left: 0; width: 100%; background: white; border-top: 1px solid #ddd; z-index: 9999; padding: 8px 0; box-shadow: 0 -3px 15px rgba(0,0,0,0.08); }}
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
            <p style="color:#666;">Connecting you to millions of opportunities worldwide.</p>
            <div class="ad-center">{ADS['AD_468X60']}</div>
            <div class="search-container">
                <input type="text" id="jobSearch" placeholder="Search by title, company, or location..." autocomplete="off">
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

if __name__ == "__main__":
    # This checks if you ran 'python content_manager.py --index'
    if len(sys.argv) > 1 and sys.argv[1] == "--index":
        generate_index()
    else:
        print("Usage: python content_manager.py --index")
