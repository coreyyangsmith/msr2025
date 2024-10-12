import csv
import requests
import os
import sys
from typing import List, Dict

# Constants
GITHUB_API_URL = "https://api.github.com"


def get_github_token() -> str:
    """
    Retrieves the GitHub Personal Access Token from an environment variable.
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("Error: Please set the GITHUB_TOKEN environment variable.")
        sys.exit(1)
    return token


def read_repositories(csv_file: str) -> List[Dict[str, str]]:
    """
    Reads the CSV file and returns a list of repositories with owner and repo names.
    """
    repositories = []
    try:
        with open(csv_file, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if "owner" in row and "repo" in row:
                    repositories.append({"owner": row["owner"], "repo": row["repo"]})
                else:
                    print("Error: CSV must contain 'owner' and 'repo' columns.")
                    sys.exit(1)
    except FileNotFoundError:
        print(f"Error: File '{csv_file}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)
    return repositories


def get_releases(owner: str, repo: str, headers: Dict[str, str]) -> List[Dict]:
    """
    Fetches the list of releases for a given repository.
    """
    releases = []
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/releases"
    params = {"per_page": 100}
    while url:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            releases_page = response.json()
            releases.extend(releases_page)
            # Check if there is a next page
            if "next" in response.links:
                url = response.links["next"]["url"]
                params = {}
            else:
                url = None
        elif response.status_code == 404:
            print(f"Warning: Repository '{owner}/{repo}' not found.")
            break
        else:
            print(
                f"Error: Failed to fetch releases for '{owner}/{repo}'. Status Code: {response.status_code}"
            )
            break
    return releases


def get_download_counts(releases: List[Dict]) -> int:
    """
    Calculates the total download count from all assets in all releases.
    """
    total_downloads = 0
    for release in releases:
        assets = release.get("assets", [])
        for asset in assets:
            download_count = asset.get("download_count", 0)
            total_downloads += download_count
    return total_downloads


def fetch_metrics(
    repositories: List[Dict[str, str]], token: str
) -> List[Dict[str, str]]:
    """
    Fetches metrics for each repository.
    """
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    metrics = []
    for repo in repositories:
        owner = repo["owner"]
        repo_name = repo["repo"]
        print(f"Processing repository: {owner}/{repo_name}")
        releases = get_releases(owner, repo_name, headers)
        download_count = get_download_counts(releases)
        metrics.append(
            {
                "owner": owner,
                "repo": repo_name,
                "release_count": len(releases),
                "download_count": download_count,
            }
        )
    return metrics


def write_metrics(csv_file: str, metrics: List[Dict[str, str]]):
    """
    Writes the metrics to a CSV file.
    """
    output_file = "repository_metrics.csv"
    fieldnames = ["owner", "repo", "release_count", "download_count"]
    try:
        with open(output_file, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for data in metrics:
                writer.writerow(data)
        print(f"Metrics written to '{output_file}'.")
    except Exception as e:
        print(f"Error writing to CSV file: {e}")
        sys.exit(1)


def main():
    csv_file = "data/cve_lifetimes_gh_filtered"
    token = get_github_token()
    repositories = read_repositories(csv_file)
    metrics = fetch_metrics(repositories, token)
    write_metrics(csv_file, metrics)


if __name__ == "__main__":
    main()
