import os
import json
import requests
from oauth2client.service_account import ServiceAccountCredentials

# 1. Get credentials from GitHub Secrets
creds_json = os.environ.get("GOOGLE_CREDENTIALS")
if not creds_json:
    print("Error: GOOGLE_CREDENTIALS secret not found")
    exit(1)

creds_dict = json.loads(creds_json)

# 2. Setup Google Indexing API
scopes = ['https://www.googleapis.com/auth/indexing']
endpoint = "https://indexing.googleapis.com/v3/urlNotifications:publish"

# 3. Get Access Token manually (This fixes the 'data' keyword error)
credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scopes)
access_token = credentials.get_access_token().access_token

# 4. Define headers
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {access_token}"
}

# 5. List of all pages in your plumbing folder to index
# Notice the "/jobs/" added to the path to match your Search Console property
urls_to_index = [
    "https://global-job-hub.github.io/jobs/plumbing/index.html",
    "https://global-job-hub.github.io/jobs/plumbing/privacy-policy.html",
    "https://global-job-hub.github.io/jobs/plumbing/terms-of-service.html"
]

# 6. Send the requests
print(f"Starting indexing for {len(urls_to_index)} URLs...")

for url in urls_to_index:
    content = {
        "url": url,
        "type": "URL_UPDATED"
    }
    try:
        response = requests.post(endpoint, json=content, headers=headers)
        print(f"URL: {url}")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        print("-" * 30)
    except Exception as e:
        print(f"Failed to index {url}: {e}")

print("Indexing process complete.")
