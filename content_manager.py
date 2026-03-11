import os
import sys
import json
import re
from datetime import datetime, timedelta

# --- CONFIG ---
# This is the base URL where your job pages will be hosted
SITE_URL = "https://global-job-hub.github.io/jobs/"

# Ad Placeholder for your template - used multiple times in the layout
AD_PLACEHOLDER = '<div class="ad-slot-placeholder" style="min-height:100px; background:#f9f9f9; display:flex; align-items:center; justify-content:center; border:1px dashed #ddd; font-size:12px; color:#aaa;">Advertisement</div>'

def slugify(text):
    """Converts job titles into URL-friendly filenames."""
    text = str(text).lower()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[-\s]+', '-', text).strip('-')

def generate_job_page(job):
    """Generates the HTML file with Google JobPosting Schema and Ad slots."""
    job_id = job.get('id', '0')
    title = job.get('title', 'Job Opening')
    company = job.get('company_name', 'Hiring Company')
    
    # Extract location from your nested JSON structure
    loc_data = job.get('job_location', {}).get('address', {})
    city = loc_data.get('addressLocality', 'Remote')
    country = loc_data.get('addressCountry', 'US')
    location_str = f"{city}, {country}"
    
    # Clean description for meta tags and schema
    description = job.get('description', '').replace('"', "'")
    apply_url = job.get('apply_url', '#')
    
    # Dates for the posting
    post_date = job.get('date_posted', datetime.utcnow().strftime("%Y-%m-%d"))
    valid_through = job.get('valid_through', (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d"))
    
    # Filename generation
    title_slug = slugify(title)
    filename = f"{title_slug}-{job_id}.html"
    
    # The HTML Content
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
      "description" : "{description}",
      "identifier": {{
        "@type": "PropertyValue",
        "name": "{company}",
        "value": "{job_id}"
      }},
      "datePosted" : "{post_date}",
      "validThrough" : "{valid_through}T23:59",
      "employmentType" : "{job.get('employment_type', 'FULL_TIME')}",
      "hiringOrganization" : {{
        "@type" : "Organization",
        "name" : "{company}",
        "sameAs" : "{SITE_URL}"
      }},
      "jobLocation": {{
        "@type": "Place",
        "address": {{
          "@type": "PostalAddress",
          "addressLocality": "{city}",
          "addressCountry": "{country}"
        }}
      }}
    }}
    </script>

    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; margin: 0; padding: 20px; color: #333; }}
        .main-container {{ max-width: 900px; margin: 0 auto; background: #fff; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); overflow: hidden; }}
        .header {{ background: #007bff; color: white; padding: 30px; text-align: center; }}
        .content-table {{ width: 100%; border-collapse: collapse; }}
        .content-table th, .content-table td {{ padding: 20px; text-align: left; border-bottom: 1px solid #eee; vertical-align: top; }}
        .content-table th {{ background: #fafafa; width: 30%; color: #666; font-weight: 600; }}
        .description-box {{ max-height: 500px; overflow-y: auto; line-height: 1.8; }}
        .ad-section {{ padding: 15px; text-align: center; background: #fff; border-bottom: 1px solid #eee; }}
        .apply-container {{ padding: 40px; text-align: center; }}
        .apply-btn {{ background: #28a745; color: white; padding: 18px 35px; text-decoration: none; border-radius: 5px; font-size: 18px; font-weight: bold; transition: background 0.2s; display: inline-block; }}
        .apply-btn:hover {{ background: #218838; }}
        footer {{ background: #343a40; color: #ccc; padding: 20px; text-align: center; font-size: 14px; }}
        footer a {{ color: #fff; text-decoration: none; margin: 0 10px; }}
    </style>
</head>
<body>

<div class="main-container">
    <div class="header">
        <h1 style="margin:0;">{title}</h1>
        <p style="margin:10px 0 0;">{company} • {location_str}</p>
    </div>

    <div class="ad-section">{AD_PLACE_HOLDER}</div>

    <table class="content-table">
        <tr>
            <th>Company</th>
            <td><strong>{company}</strong></td>
        </tr>
        <tr>
            <th>Job Location</th>
            <td>{location_str}</td>
        </tr>
        
        <tr><td colspan="2" class="ad-section">{AD_PLACEHOLDER}</td></tr>

        <tr>
            <th>Job Description</th>
            <td><div class="description-box">{description}</div></td>
        </tr>
        <tr>
            <th>Employment Type</th>
            <td>{job.get('employment_type', 'Full-Time')}</td>
        </tr>

        <tr><td colspan="2" class="ad-section">{AD_PLACEHOLDER}</td></tr>

        <tr>
            <th>Posted On</th>
            <td>{post_date}</td>
        </tr>
        <tr>
            <th>Closing Date</th>
            <td>{valid_through}</td>
        </tr>
    </table>

    <div class="ad-section">{AD_PLACEHOLDER}</div>

    <div class="apply-container">
        <p>Interested in this position? Click the button below to apply directly on the official platform.</p>
        <a href="{apply_url}" class="apply-btn" target="_blank">Apply Now &raquo;</a>
    </div>

    <footer>
        <p>© 2026 Global Job Hub. All rights reserved.</p>
        <p>
            <a href="{SITE_URL}">Home</a> | 
            <a href="{SITE_URL}privacy.html">Privacy Policy</a> | 
            <a href="{SITE_URL}contact.html">Contact</a>
        </p>
    </footer>
</div>

</body>
</html>"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_template)
    
    return filename

def main():
    # Expecting the JSON file path as an argument
    if len(sys.argv) < 2:
        print("❌ Usage: python content_manager.py your_jobs_file.json")
        sys.exit(1)

    input_file = sys.argv[1]
    
    if not os.path.exists(input_file):
        print(f"❌ Error: File '{input_file}' not found.")
        sys.exit(1)

    print(f"📖 Loading jobs from {input_file}...")
    with open(input_file, "r", encoding="utf-8") as f:
        jobs_list = json.load(f)

    # We will store the full URLs of generated pages here to pass to the indexer
    generated_urls = []

    for job in jobs_list:
        try:
            filename = generate_job_page(job)
            full_url = f"{SITE_URL}{filename}"
            generated_urls.append(full_url)
            print(f"📄 Created: {filename}")
        except Exception as e:
            print(f"⚠️ Failed to process job {job.get('id')}: {e}")

    # Write all URLs to pending_urls.txt for the indexer.py script
    with open("pending_urls.txt", "w", encoding="utf-8") as f:
        for url in generated_urls:
            f.write(url + "\n")

    print(f"✅ Finished. {len(generated_urls)} job pages ready for indexing.")

if __name__ == "__main__":
    main()
