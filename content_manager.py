import os
import sys
import json
import requests
import datetime
import re
import hashlib

# --- CONFIG ---
BUFFER_FILE = "job_buffer.json"
JOOBLE_KEY = os.environ.get("JOOBLE_API_KEY")
SITE_URL = "https://global-job-hub.github.io/jobs/"

# Fetch Ad Secrets (same as before)
ADS = {
    "AD_728x90": os.environ.get("AD_728x90", ""),
    "AD_300x250": os.environ.get("AD_300x250", ""),
    "AD_468x60": os.environ.get("AD_468x60", ""),
    "AD_160x600": os.environ.get("AD_160x600", ""),
    "AD_160x300": os.environ.get("AD_160x300", ""),
    "AD_320x50": os.environ.get("AD_320x50", ""),
    "AD_NATIVE": os.environ.get("AD_NATIVE", "")
}

def load_buffer():
    if os.path.exists(BUFFER_FILE):
        with open(BUFFER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_buffer(jobs):
    with open(BUFFER_FILE, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=4)

def generate_fingerprint(job):
    data_string = f"{job.get('title')}{job.get('company')}{job.get('snippet')}{job.get('location')}"
    return hashlib.md5(data_string.encode('utf-8')).hexdigest()

def slugify(text):
    text = str(text).lower()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[-\s]+', '-', text).strip('-')

def generate_job_page(job):
    # (The HTML generation code you already have remains the same here)
    # Ensure it returns filename or None based on exists check
    title_slug = slugify(job.get('title'))
    filename = f"{title_slug}-{job.get('id')}.html"
    
    if os.path.exists(filename):
        return None
    
    # ... [Insert the professional HTML Template from previous response here] ...
    # Make sure to include the fingerprint in the HTML comment
    return filename

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--generate"
    
    if mode == "--generate":
        buffer_jobs = load_buffer()
        
        # 1. If buffer is empty, fetch new jobs from Jooble
        if not buffer_jobs:
            print("📭 Buffer empty. Calling Jooble API...")
            if not JOOBLE_KEY: return
            url = f"https://jooble.org/api/{JOOBLE_KEY}"
            res = requests.post(url, json={"keywords": "remote", "location": ""})
            buffer_jobs = res.json().get('jobs', [])
            print(f"📥 Received {len(buffer_jobs)} jobs from Jooble.")
        else:
            print(f"📦 Using {len(buffer_jobs)} jobs from existing buffer.")

        # 2. Extract 20 jobs to process now
        jobs_to_process = buffer_jobs[:20]
        remaining_jobs = buffer_jobs[20:]
        
        new_urls = []
        unique_count = 0
        
        for job in jobs_to_process:
            fname = generate_job_page(job)
            if fname:
                new_urls.append(f"{SITE_URL}{fname}")
                unique_count += 1
        
        # 3. Save the leftovers back to the buffer for the next run
        save_buffer(remaining_jobs)
        
        # 4. Save pending URLs for indexing
        with open("pending_urls.txt", "w") as f:
            for u in new_urls: f.write(u + "\n")
            
        print(f"✅ Created {unique_count} new pages. {len(remaining_jobs)} jobs left in buffer.")

    elif mode == "--index":
        # ... (Your indexing logic)
        pass

if __name__ == "__main__":
    main()
