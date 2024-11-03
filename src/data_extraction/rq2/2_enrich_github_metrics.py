import csv
import logging
import requests
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, Optional
from datetime import datetime
from dateutil.parser import parse as parse_date

from ...utils.config import RQ2_2_INPUT, RQ2_2_OUTPUT, GITHUB_API_URL, GITHUB_HEADERS


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
# Fetch GitHub token from environment variable for authentication (optional)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Set your token as an environment variable

# Headers for GitHub API requests
if GITHUB_TOKEN:
    GITHUB_HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"


def get_license(owner: str, repo: str) -> Optional[str]:
    """
    Fetch the license of a GitHub repository using the GitHub API.

    Args:
        owner (str): The owner of the repository.
        repo (str): The repository name.

    Returns:
        Optional[str]: The license name if available, else None.
    """
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/license"
    try:
        response = requests.get(url, headers=GITHUB_HEADERS)
        if response.status_code == 200:
            data = response.json()
            license_info = data.get("license")
            if license_info:
                return license_info.get("name")
            else:
                logging.warning(f"No license information found for {owner}/{repo}.")
                return None
        elif response.status_code == 404:
            logging.warning(f"Repository {owner}/{repo} not found or no license.")
            return None
        elif response.status_code == 403 and "rate limit" in response.text.lower():
            reset_time = response.headers.get("X-RateLimit-Reset")
            if reset_time:
                sleep_seconds = int(reset_time) - int(time.time()) + 5  # Adding buffer
                if sleep_seconds > 0:
                    logging.warning(
                        f"Rate limit exceeded. Sleeping for {sleep_seconds} seconds."
                    )
                    time.sleep(sleep_seconds)
                    return get_license(owner, repo)  # Retry after sleeping
            else:
                logging.error("Rate limit exceeded and reset time not found.")
                return None
        else:
            logging.error(
                f"Error fetching license for {owner}/{repo}: {response.status_code} {response.text}"
            )
            return None
    except requests.RequestException as e:
        logging.error(f"Request exception for {owner}/{repo}: {e}")
        return None


def get_start_date(owner: str, repo: str) -> Optional[str]:
    """
    Fetch the creation date of a GitHub repository using the GitHub API.

    Args:
        owner (str): The owner of the repository.
        repo (str): The repository name.

    Returns:
        Optional[str]: The creation date if available, else None.
    """
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}"
    try:
        response = requests.get(url, headers=GITHUB_HEADERS)
        if response.status_code == 200:
            data = response.json()
            created_at = data.get("created_at")
            if created_at:
                return created_at
            else:
                logging.warning(f"No creation date found for {owner}/{repo}.")
                return None
        elif response.status_code == 404:
            logging.warning(f"Repository {owner}/{repo} not found.")
            return None
        elif response.status_code == 403 and "rate limit" in response.text.lower():
            reset_time = response.headers.get("X-RateLimit-Reset")
            if reset_time:
                sleep_seconds = int(reset_time) - int(time.time()) + 5  # Adding buffer
                if sleep_seconds > 0:
                    logging.warning(
                        f"Rate limit exceeded. Sleeping for {sleep_seconds} seconds."
                    )
                    time.sleep(sleep_seconds)
                    return get_start_date(owner, repo)  # Retry after sleeping
            else:
                logging.error("Rate limit exceeded and reset time not found.")
                return None
        else:
            logging.error(
                f"Error fetching start date for {owner}/{repo}: {response.status_code} {response.text}"
            )
            return None
    except requests.RequestException as e:
        logging.error(f"Request exception for {owner}/{repo}: {e}")
        return None


def get_open_issues_count(
    owner: str, repo: str, start_date: str, end_date: str
) -> Optional[int]:
    """
    Fetch the count of open issues created between start_date and end_date.

    Args:
        owner (str): The owner of the repository.
        repo (str): The repository name.
        start_date (str): The start date in ISO format.
        end_date (str): The end date in ISO format.

    Returns:
        Optional[int]: The count of open issues, else None.
    """
    url = f"{GITHUB_API_URL}/search/issues"
    query = (
        f"repo:{owner}/{repo} type:issue state:open created:{start_date}..{end_date}"
    )
    params = {"q": query, "per_page": 1}

    try:
        response = requests.get(url, headers=GITHUB_HEADERS, params=params)
        if response.status_code == 200:
            data = response.json()
            total_count = data.get("total_count")
            if total_count is not None:
                return total_count
            else:
                logging.warning(f"No issue count found for {owner}/{repo}.")
                return None
        elif response.status_code == 403 and "rate limit" in response.text.lower():
            reset_time = response.headers.get("X-RateLimit-Reset")
            if reset_time:
                sleep_seconds = int(reset_time) - int(time.time()) + 5  # Adding buffer
                if sleep_seconds > 0:
                    logging.warning(
                        f"Rate limit exceeded. Sleeping for {sleep_seconds} seconds."
                    )
                    time.sleep(sleep_seconds)
                    return get_open_issues_count(
                        owner, repo, start_date, end_date
                    )  # Retry after sleeping
            else:
                logging.error("Rate limit exceeded and reset time not found.")
                return None
        else:
            logging.error(
                f"Error fetching open issues for {owner}/{repo}: {response.status_code} {response.text}"
            )
            return None
    except requests.RequestException as e:
        logging.error(f"Request exception for {owner}/{repo}: {e}")
        return None


def check_for_test_folder(owner: str, repo: str) -> Optional[bool]:
    """
    Check if the repository has a 'test' or 'tests' folder anywhere in the repository.

    Args:
        owner (str): The owner of the repository.
        repo (str): The repository name.

    Returns:
        Optional[bool]: True if 'test' or 'tests' folder exists, False otherwise.
    """
    # Step 1: Get the default branch
    repo_url = f"{GITHUB_API_URL}/repos/{owner}/{repo}"
    try:
        repo_response = requests.get(repo_url, headers=GITHUB_HEADERS)
        if repo_response.status_code == 200:
            repo_data = repo_response.json()
            default_branch = repo_data.get("default_branch")
            if not default_branch:
                logging.warning(f"No default branch found for {owner}/{repo}.")
                return None
        elif repo_response.status_code == 404:
            logging.warning(f"Repository {owner}/{repo} not found.")
            return None
        elif (
            repo_response.status_code == 403
            and "rate limit" in repo_response.text.lower()
        ):
            reset_time = repo_response.headers.get("X-RateLimit-Reset")
            if reset_time:
                sleep_seconds = int(reset_time) - int(time.time()) + 5  # Adding buffer
                if sleep_seconds > 0:
                    logging.warning(
                        f"Rate limit exceeded. Sleeping for {sleep_seconds} seconds."
                    )
                    time.sleep(sleep_seconds)
                    return check_for_test_folder(owner, repo)  # Retry after sleeping
            else:
                logging.error("Rate limit exceeded and reset time not found.")
                return None
        else:
            logging.error(
                f"Error fetching repository info for {owner}/{repo}: {repo_response.status_code} {repo_response.text}"
            )
            return None

        # Step 2: Get the commit sha of the default branch
        branch_url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/branches/{default_branch}"
        branch_response = requests.get(branch_url, headers=GITHUB_HEADERS)
        if branch_response.status_code == 200:
            branch_data = branch_response.json()
            commit_sha = branch_data["commit"]["sha"]
        elif branch_response.status_code == 404:
            logging.warning(f"Branch {default_branch} not found for {owner}/{repo}.")
            return None
        elif (
            branch_response.status_code == 403
            and "rate limit" in branch_response.text.lower()
        ):
            reset_time = branch_response.headers.get("X-RateLimit-Reset")
            if reset_time:
                sleep_seconds = int(reset_time) - int(time.time()) + 5  # Adding buffer
                if sleep_seconds > 0:
                    logging.warning(
                        f"Rate limit exceeded. Sleeping for {sleep_seconds} seconds."
                    )
                    time.sleep(sleep_seconds)
                    return check_for_test_folder(owner, repo)  # Retry after sleeping
            else:
                logging.error("Rate limit exceeded and reset time not found.")
                return None
        else:
            logging.error(
                f"Error fetching branch info for {owner}/{repo}: {branch_response.status_code} {branch_response.text}"
            )
            return None

        # Step 3: Get the repository tree
        tree_url = (
            f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/trees/{commit_sha}?recursive=1"
        )
        tree_response = requests.get(tree_url, headers=GITHUB_HEADERS)
        if tree_response.status_code == 200:
            tree_data = tree_response.json()
            if "tree" in tree_data:
                test_folder_names = ["test", "tests"]
                for item in tree_data["tree"]:
                    if item["type"] == "tree":
                        folder_name = item["path"].split("/")[-1].lower()
                        if folder_name in test_folder_names:
                            return True
                return False
            else:
                logging.warning(f"No tree data found for {owner}/{repo}.")
                return None
        elif tree_response.status_code == 404:
            logging.warning(f"Tree not found for {owner}/{repo}.")
            return None
        elif (
            tree_response.status_code == 403
            and "rate limit" in tree_response.text.lower()
        ):
            reset_time = tree_response.headers.get("X-RateLimit-Reset")
            if reset_time:
                sleep_seconds = int(reset_time) - int(time.time()) + 5  # Adding buffer
                if sleep_seconds > 0:
                    logging.warning(
                        f"Rate limit exceeded. Sleeping for {sleep_seconds} seconds."
                    )
                    time.sleep(sleep_seconds)
                    return check_for_test_folder(owner, repo)  # Retry after sleeping
            else:
                logging.error("Rate limit exceeded and reset time not found.")
                return None
        else:
            logging.error(
                f"Error fetching tree for {owner}/{repo}: {tree_response.status_code} {tree_response.text}"
            )
            return None

    except requests.RequestException as e:
        logging.error(f"Request exception for {owner}/{repo}: {e}")
        return None


# Define field processors
FIELD_PROCESSORS = {
    "github_license": get_license,
    "github_start_date": get_start_date,
    "has_test_folder": check_for_test_folder,  # Added this line
}


def process_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single CSV row to fetch additional GitHub information.

    Args:
        row (Dict[str, Any]): A dictionary representing a row from the CSV.

    Returns:
        Dict[str, Any]: The updated row with new fields.
    """
    owner = row.get("github_owner")
    repo = row.get("github_repo")
    cve_publish_date = row.get("cve_publish_date")

    if not owner or not repo:
        logging.warning(f"Missing owner or repo in row: {row}")
        # Set None for all fields in FIELD_PROCESSORS
        for field_name in FIELD_PROCESSORS:
            row[field_name] = None
        row["github_open_issues"] = None
        return row

    for field_name, func in FIELD_PROCESSORS.items():
        result = func(owner, repo)
        row[field_name] = result
        logging.info(f"Processed {owner}/{repo}: {field_name} - {result}")

    # Process github_open_issues
    start_date = row.get("github_start_date")
    end_date = cve_publish_date

    if start_date and end_date:
        try:
            # Parse start_date and end_date using dateutil.parser
            start_date_iso = parse_date(start_date).date().isoformat()
            end_date_iso = parse_date(end_date).date().isoformat()

            open_issues_count = get_open_issues_count(
                owner, repo, start_date_iso, end_date_iso
            )
            row["github_open_issues"] = open_issues_count
            logging.info(
                f"Processed {owner}/{repo}: github_open_issues - {open_issues_count}"
            )
        except (ValueError, TypeError) as e:
            logging.error(f"Date parsing error for {owner}/{repo}: {e}")
            row["github_open_issues"] = None
    else:
        logging.warning(f"Missing start_date or end_date for {owner}/{repo}.")
        row["github_open_issues"] = None

    return row


def process_csv(input_csv: str, output_csv: str, max_workers: int = 5):
    """
    Read the input CSV, process each repository to fetch additional information, and write to output CSV.

    Args:
        input_csv (str): Path to the input CSV file.
        output_csv (str): Path to the output CSV file.
        max_workers (int): Maximum number of threads for concurrent processing.
    """
    # Read all rows from the input CSV
    with open(input_csv, newline="", encoding="utf-8") as csvfile_in:
        reader = csv.DictReader(csvfile_in)
        fieldnames = reader.fieldnames.copy()
        for field_name in FIELD_PROCESSORS.keys():
            if field_name not in fieldnames:
                fieldnames.append(field_name)
        # Add 'github_open_issues' to fieldnames if not present
        if "github_open_issues" not in fieldnames:
            fieldnames.append("github_open_issues")
        rows = list(reader)

    logging.info(f"Total repositories to process: {len(rows)}")

    # Use ThreadPoolExecutor to process repositories concurrently
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_row = {executor.submit(process_row, row): row for row in rows}

        for future in as_completed(future_to_row):
            row = future_to_row[future]
            try:
                updated_row = future.result()
                # You can handle the updated_row here if needed
            except Exception as e:
                logging.error(f"Error processing row {row}: {e}")

    # Write the updated rows to the output CSV
    with open(output_csv, "w", newline="", encoding="utf-8") as csvfile_out:
        writer = csv.DictWriter(csvfile_out, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    logging.info(f"Finished processing. Output written to {output_csv}")


def main():
    input_csv = RQ2_2_INPUT
    output_csv = RQ2_2_OUTPUT
    process_csv(input_csv, output_csv)


if __name__ == "__main__":
    main()
