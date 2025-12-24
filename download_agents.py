import os
import requests
import base64
from datetime import datetime
import logging
import sqlite3

logger = logging.getLogger(__name__)

db_path= "data.db"

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------
ORG = "rl2526"                     # GitHub organization name
ASSIGNMENT_PREFIX = "rl-exercise-d-" # student repo prefix
WORKFLOW_NAME = "Evaluate"        # name of the student workflow


TOKEN_READ = os.environ.get("READ")

if TOKEN_READ is None:
    raise RuntimeError("READ environment variable not set")

HEADERS_READ = {
    "Authorization": f"Bearer {TOKEN_READ}",
    "Accept": "application/vnd.github+json",
}

# --------------------------------------------------
# GITHUB API HELPERS
# --------------------------------------------------


def get_all_user_names():
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT name FROM users")
    rows = cur.fetchall()

    conn.close()

    return {row[0] for row in rows}


def list_repos():
    """List all repos in the org that match the assignment prefix."""
    repos = []
    page = 1

    user_names = get_all_user_names()

    while True:
        url = f"https://api.github.com/orgs/{ORG}/repos?per_page=100&page={page}"
        r = requests.get(url, headers=HEADERS_READ)
        r.raise_for_status()
        batch = r.json()

        if not batch:
            break

        for repo in batch:
            repo_name = repo["name"]
            print(f"student repo name: {repo_name}")
            if repo_name.startswith(ASSIGNMENT_PREFIX):
                repo_name = repo_name.replace(ASSIGNMENT_PREFIX, "")
                if repo_name in user_names:
                    repos.append(repo)
        page += 1
    return repos


def latest_commit(name):

    # holt Commits vom Default-Branch (meist main)
    url = f"https://api.github.com/repos/{ORG}/{name}/commits"

    print(f"Student Repo Commits URL: {url}")
    r = requests.get(url, headers=HEADERS_READ)
    r.raise_for_status()

    commits = r.json()
    if not commits:
        return None

    iso = commits[0]["commit"]["committer"]["date"]   
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return int(dt.timestamp())

def get_last_db_timestamp(username):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT last_updated FROM users WHERE name = ?", (username,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

def is_newer_than_db(repo):
    commit_ts = latest_commit(repo)
    db_ts = get_last_db_timestamp(repo.replace(ASSIGNMENT_PREFIX, ""))

    if commit_ts is None:
        return False          
    if db_ts is None:
        return True           

    return commit_ts > db_ts  


def download_agent(repo):
    name = repo["name"]

    url = f"https://api.github.com/repos/{ORG}/{name}/contents/submission/agent.py"

    r = requests.get(url, headers=HEADERS_READ)
    r.raise_for_status()

    data = r.json()

    if data.get("type") != "file":
        return None

    content_b64 = data["content"]
    agent_code = base64.b64decode(content_b64).decode("utf-8")

    return agent_code

# --------------------------------------------------
# MAIN
# --------------------------------------------------
def main():
    for repo in list_repos(): 
        repo_name = repo["name"]
        print(f"Processing {repo}")

        if not is_newer_than_db(repo_name):
            continue

        result = download_agent(repo)
        if not result:
            print(" No agent.py")
            continue

        with open(f"/agents/{repo_name}.py", "w") as f:
            f.write(result)

if __name__ == "__main__":
    main()
