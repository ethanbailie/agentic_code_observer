import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os

load_dotenv()

owner = "ethanbailie"
repo = "agentic_code_observer"
token = os.getenv("GITHUB_TOKEN")


## build the pr url
pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github.v3+json"
}

## calculate the timestamp for 24 hours ago
recency = datetime.now(timezone.utc) - timedelta(days=1)
recency_str = recency.isoformat() + "Z"

## pagination params
params = {
    "state": "all",
    "per_page": 100
}

## function to fetch all PRs
def fetch_recent_prs():
    all_recent_prs = []
    page = 1
    while True:
        params['page'] = page
        response = requests.get(pr_url, headers=headers, params=params)
        prs = response.json()

        ## filter on the recency param
        recent_prs = [pr for pr in prs if pr["updated_at"] >= recency_str]

        ## break if no more recent PRs are found
        if not recent_prs:
            break

        all_recent_prs.extend(recent_prs)
        page += 1
    return all_recent_prs

## use the fetch function to grab prs
recent_pull_requests = fetch_recent_prs()

## print out details for each recent merged PR
for pr in recent_pull_requests:
    if pr.get("merged_at"):
        print(f"Title: {pr['title']}")
        print(f"State: {pr['state']}")
        print(f"Description: {pr['body']}")
        print(f"Updated At: {pr['updated_at']}")
        print(f"URL: {pr['html_url']}")

        ## fetch and display merge description if the PR was merged
        merge_commit_sha = pr["merge_commit_sha"]
        commit_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{merge_commit_sha}"
        commit_response = requests.get(commit_url, headers=headers).json()
        merge_description = commit_response.get("commit", {}).get("message", "")
        print(f"Merge Description: {merge_description}")