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

credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scopes)
session = credentials.authorize(requests.Session())

# 3. Define the URL to index
url_to_index = "https://global-job-hub.github.io/jobs/plumbing/index.html"

# 4. Send the request
content = {
  "url": url_to_index,
  "type": "URL_UPDATED"
}

response = session.post(endpoint, json=content)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")
