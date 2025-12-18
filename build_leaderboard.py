import json
import os
import requests
import zipfile
from io import BytesIO
from datetime import datetime

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------
ORG = "rl2526"                     # GitHub organization name
ASSIGNMENT_PREFIX = "exercise-d-" # student repo prefix
WORKFLOW_NAME = "Update Leaderboard"        # name of the student workflow
OUTPUT_FILE = "leaderboard.json"


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
def list_repos():
    """List all repos in the org that match the assignment prefix."""
    repos = []
    page = 1

    while True:
        url = f"https://api.github.com/orgs/{ORG}/repos?per_page=100&page={page}"
        r = requests.get(url, headers=HEADERS_READ)
        r.raise_for_status()
        batch = r.json()

        if not batch:
            break

        for repo in batch:
            repo_name = repo["name"]
            if repo["name"].startswith(ASSIGNMENT_PREFIX):
                # Keep student info as part of repo["name"]
                repos.append(repo)

        page += 1

    return repos


def latest_successful_run(repo):
    """Get latest successful workflow run."""
    url = f"https://api.github.com/repos/{ORG}/{repo}/actions/runs"
    r = requests.get(url, headers=HEADERS_READ)
    r.raise_for_status()

    for run in r.json().get("workflow_runs", []):
        if run["name"] == WORKFLOW_NAME and run["conclusion"] == "success":
            return run

    return None


def download_result(repo, run_id):
    """Download and extract result.json from artifact."""
    url = f"https://api.github.com/repos/{ORG}/{repo}/actions/runs/{run_id}/artifacts"
    r = requests.get(url, headers=HEADERS_READ)
    r.raise_for_status()

    artifacts = r.json().get("artifacts", [])
    artifact = next((a for a in artifacts if a["name"] == "result"), None)

    if artifact is None:
        return None

    r = requests.get(artifact["archive_download_url"], headers=HEADERS_READ)
    r.raise_for_status()

    with zipfile.ZipFile(BytesIO(r.content)) as z:
        for name in z.namelist():
            if name.endswith("result.json"):
                return json.loads(z.read(name))

    return None


# --------------------------------------------------
# MAIN
# --------------------------------------------------
def main():
    entries = []

    for repo in list_repos():
        repo_name = repo["name"]
        print(f"Processing {repo}")

        run = latest_successful_run(repo)
        if not run:
            print("  No successful run found")
            continue

        result = download_result(repo, run["id"])
        if not result:
            print("  No result.json artifact")
            continue

        # Compute average over all average_return values
        if result:
            avg_return = sum(p["average_return"] for p in result) / len(result)
        else:
            avg_return = 0.0

        student_name = repo_name.rsplit("-", 1)[-1]

        entries.append({
            "repo": repo_name,
            "student_name": student_name,
            "avg_return": avg_return,
            "updated_at": run["updated_at"],
        })

    # sort by score descending
    entries.sort(key=lambda e: (-e["avg_return"], e["repo"]))

    with open(OUTPUT_FILE, "w") as f:
        json.dump(
            {
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "entries": entries,
            },
            f,
            indent=2,
        )

    print(f"Wrote {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
