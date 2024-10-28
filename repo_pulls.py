import requests
from dotenv import load_dotenv
import os

load_dotenv()

owner = "ethanbailie"
repo = "agentic_code_observer"
token = os.getenv("GITHUB_TOKEN")

url = f"https://api.github.com/repos/{owner}/{repo}/pulls"

headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github.v3+json"
}

params = {
    "state": "all",
    "per_page": 100
}

def fetch_all_prs():
    all_prs = []
    page = 1
    while True:
        params['page'] = page
        response = requests.get(url, headers=headers, params=params)
        prs = response.json()

        if not prs:
            break

        all_prs.extend(prs)
        page += 1
    
    return all_prs

pull_requests = fetch_all_prs()

for pr in pull_requests:
    print(f"Title: {pr['title']}, State: {pr['state']}, URL: {pr['html_url']}")
