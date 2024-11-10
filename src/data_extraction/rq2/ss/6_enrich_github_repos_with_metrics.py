import csv
import requests
import sys
import os
import logging
from urllib.parse import urlparse
from time import sleep

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# GitHub API base URL
GITHUB_API_URL = "https://api.github.com"

# Get GitHub token from environment variable
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Headers for GitHub API requests
HEADERS = {"Accept": "application/vnd.github.v3+json"}

print(GITHUB_TOKEN)
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"
else:
    logging.warning("No GitHub token found. You may encounter rate limiting.")


def parse_github_url(url):
    """
    Parses the GitHub URL and returns the owner and repo name.
    """
    try:
        parsed = urlparse(url)
        if parsed.netloc not in ["github.com", "www.github.com"]:
            raise ValueError("URL is not a GitHub URL.")
        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) < 2:
            raise ValueError("URL does not contain owner and repository.")
        owner, repo = path_parts[0], path_parts[1]
        # Remove .git suffix if present
        if repo.endswith(".git"):
            repo = repo[:-4]
        return owner, repo
    except Exception as e:
        logging.error(f"Error parsing URL '{url}': {e}")
        return None, None


def get_repo_metrics(owner, repo):
    """
    Fetches repository metrics from GitHub API.
    Returns a dictionary with various metrics.
    """
    metrics = {
        "stars": 0,
        "forks": 0,
        "open_issues": 0,
        "contributors": 0,
        "watchers": 0,
        "downloads": 0,
        "dependencies": 0,
        "license": "N/A",
        "documentation": "N/A",
        "test_code": "N/A",
        "build_status": "N/A",
        "vulnerabilities": 0,
        "badges": "N/A",
        "website": "N/A",
        "releases": 0,
        "closed_issues": 0,
        "commit_frequency": 0,
        "usage": "N/A",
    }

    while True:
        # Get repository details
        repo_url = f"{GITHUB_API_URL}/repos/{owner}/{repo}"
        try:
            response = requests.get(repo_url, headers=HEADERS)
            if response.status_code == 404:
                logging.error(f"Repository {owner}/{repo} not found.")
                return metrics
            elif response.status_code == 403:
                logging.error("Rate limit exceeded. Retrying in 5 minutes...")
                sleep(300)
                continue
            response.raise_for_status()
            repo_data = response.json()
            print(repo_data)
            metrics["stars"] = repo_data.get("stargazers_count", 0)
            metrics["forks"] = repo_data.get("forks_count", 0)
            metrics["open_issues"] = repo_data.get("open_issues_count", 0)
            metrics["watchers"] = repo_data.get("subscribers_count", 0)
            metrics["license"] = (
                repo_data.get("license")["name"] if repo_data.get("license") else "N/A"
            )
            metrics["website"] = repo_data.get("homepage", "N/A")
            break
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching repo data for {owner}/{repo}: {e}")
            return metrics

    # Get contributors count
    while True:
        contributors_url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/contributors"
        params = {"per_page": 1, "anon": "true"}
        try:
            response = requests.get(contributors_url, headers=HEADERS, params=params)
            if response.status_code == 404:
                logging.error(f"Contributors not found for {owner}/{repo}.")
                return metrics
            elif response.status_code == 403:
                logging.error("Rate limit exceeded. Retrying in 5 minutes...")
                sleep(300)
                continue
            response.raise_for_status()
            if "Link" in response.headers:
                links = response.headers["Link"]
                # Extract the last page number from the Link header
                last_page = 1
                for link in links.split(","):
                    if 'rel="last"' in link:
                        last_page = int(link.split("&page=")[-1].split(">")[0])
                metrics["contributors"] = last_page
            else:
                # If no Link header, check the number of contributors returned
                contributors = response.json()
                metrics["contributors"] = len(contributors)
            break
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching contributors for {owner}/{repo}: {e}")
            return metrics

    # Get releases count
    while True:
        releases_url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/releases"
        params = {"per_page": 1}
        try:
            response = requests.get(releases_url, headers=HEADERS, params=params)
            if response.status_code == 403:
                logging.error("Rate limit exceeded. Retrying in 5 minutes...")
                sleep(300)
                continue
            response.raise_for_status()
            if "Link" in response.headers:
                links = response.headers["Link"]
                last_page = 1
                for link in links.split(","):
                    if 'rel="last"' in link:
                        last_page = int(link.split("&page=")[-1].split(">")[0])
                metrics["releases"] = last_page
            else:
                releases = response.json()
                metrics["releases"] = len(releases)
            break
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching releases for {owner}/{repo}: {e}")
            return metrics

    # Get closed issues count
    while True:
        issues_url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues"
        params = {"state": "closed", "per_page": 1}
        try:
            response = requests.get(issues_url, headers=HEADERS, params=params)
            if response.status_code == 403:
                logging.error("Rate limit exceeded. Retrying in 5 minutes...")
                sleep(300)
                continue
            response.raise_for_status()
            if "Link" in response.headers:
                links = response.headers["Link"]
                last_page = 1
                for link in links.split(","):
                    if 'rel="last"' in link:
                        last_page = int(link.split("&page=")[-1].split(">")[0])
                metrics["closed_issues"] = last_page
            else:
                issues = response.json()
                metrics["closed_issues"] = len(issues)
            break
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching closed issues for {owner}/{repo}: {e}")
            return metrics

    # Additional metrics like badges, build status, vulnerabilities, etc., can be gathered using other services or by parsing README files.

    return metrics


def process_csv(input_file, output_file):
    """
    Processes the input CSV and writes the output CSV with additional metrics.
    """
    with open(input_file, newline="", encoding="utf-8") as csv_in, open(
        output_file, "w", newline="", encoding="utf-8"
    ) as csv_out:
        reader = csv.reader(csv_in)
        writer = csv.writer(csv_out)

        # Write header
        header = [
            "group",
            "name",
            "version",
            "github_url",
            "stars",
            "forks",
            "open_issues",
            "contributors",
            "watchers",
            "downloads",
            "dependencies",
            "license",
            "documentation",
            "test_code",
            "build_status",
            "vulnerabilities",
            "badges",
            "website",
            "releases",
            "closed_issues",
            "commit_frequency",
            "usage",
        ]
        writer.writerow(header)

        for row in reader:
            if len(row) < 4:
                logging.warning(f"Skipping incomplete row: {row}")
                continue
            group, name, version, url = row[:4]
            owner, repo = parse_github_url(url)
            if not owner or not repo:
                logging.warning(f"Skipping row due to invalid URL: {row}")
                metrics = {
                    "stars": 0,
                    "forks": 0,
                    "open_issues": 0,
                    "contributors": 0,
                    "watchers": 0,
                    "downloads": 0,
                    "dependencies": 0,
                    "license": "N/A",
                    "documentation": "N/A",
                    "test_code": "N/A",
                    "build_status": "N/A",
                    "vulnerabilities": 0,
                    "badges": "N/A",
                    "website": "N/A",
                    "releases": 0,
                    "closed_issues": 0,
                    "commit_frequency": 0,
                    "usage": "N/A",
                }
            else:
                metrics = get_repo_metrics(owner, repo)
                # To respect rate limits, sleep if not authenticated
                if not GITHUB_TOKEN:
                    sleep(1)  # Adjust sleep time as needed
            output_row = [
                group,
                name,
                version,
                url,
                metrics["stars"],
                metrics["forks"],
                metrics["open_issues"],
                metrics["contributors"],
                metrics["watchers"],
                metrics["downloads"],
                metrics["dependencies"],
                metrics["license"],
                metrics["documentation"],
                metrics["test_code"],
                metrics["build_status"],
                metrics["vulnerabilities"],
                metrics["badges"],
                metrics["website"],
                metrics["releases"],
                metrics["closed_issues"],
                metrics["commit_frequency"],
                metrics["usage"],
            ]
            writer.writerow(output_row)
            logging.info(f"Processed {owner}/{repo}: {metrics}")

    logging.info(f"Output written to {output_file}")


def main():
    input_file = "data/unique_filtered_github_artifacts.csv"
    output_file = "data/enriched_gh_artifacts.csv"

    if not os.path.isfile(input_file):
        logging.error(f"Input file '{input_file}' does not exist.")
        sys.exit(1)

    process_csv(input_file, output_file)


if __name__ == "__main__":
    main()
