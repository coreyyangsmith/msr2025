import csv
import logging
import re
import requests
import time
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple

from ...utils.config import (
    RQ2_1_INPUT,
    RQ2_1_OUTPUT,
    RQ2_1_FILTERED_OUTPUT,
    RQ2_1_NON_GITHUB_OUTPUT,  # New configuration constant for the third file
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

"""
Parses POM XML to find matching GitHub URLs and extracts GitHub owner and repository.
"""


def get_pom(
    group_id: str, artifact_id: str, version: str, retries: int = 3
) -> Optional[str]:
    """
    Constructs the POM URL and retrieves the POM file content with retries.
    """
    group_path = group_id.replace(".", "/")
    url = f"https://repo1.maven.org/maven2/{group_path}/{artifact_id}/{version}/{artifact_id}-{version}.pom"
    backoff = 1  # Initial backoff delay in seconds
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                logging.debug(
                    f"Successfully retrieved POM for {group_id}:{artifact_id}:{version}"
                )
                return response.text
            else:
                logging.warning(
                    f"Attempt {attempt}: Failed to retrieve POM for {group_id}:{artifact_id}:{version} "
                    f"- Status Code: {response.status_code}"
                )
        except requests.RequestException as e:
            logging.warning(
                f"Attempt {attempt}: Error fetching POM for {group_id}:{artifact_id}:{version} - {e}"
            )

        if attempt < retries:
            time.sleep(backoff)
            backoff *= 2  # Exponential backoff
    logging.error(f"Exceeded maximum retries for {group_id}:{artifact_id}:{version}")
    return None


def get_scm_url_from_pom(pom_xml: str) -> Optional[str]:
    """
    Parses the POM XML to find the SCM URL in the SCM section.
    """
    try:
        root = ET.fromstring(pom_xml)

        # Extract the namespace, if any
        namespace_match = re.match(r"\{(.*)\}", root.tag)
        namespace = namespace_match.group(1) if namespace_match else ""
        ns = {"ns": namespace} if namespace else {}

        # Search for the SCM element
        scm = root.find(".//ns:scm", ns) if namespace else root.find(".//scm")
        if scm is not None:
            scm_url = _extract_scm_url(scm, ns)
            return scm_url
        return None
    except ET.ParseError as e:
        logging.error(f"Error parsing POM XML: {e}")
        return None


def _extract_scm_url(scm_element: ET.Element, ns: Dict[str, str]) -> Optional[str]:
    """
    Extracts the SCM URL from the SCM element.
    """
    tags = ["url", "connection", "developerConnection"]
    for tag in tags:
        if ns:
            url_elem = scm_element.find(f"ns:{tag}", ns)
        else:
            url_elem = scm_element.find(tag)
        if url_elem is not None and url_elem.text:
            return url_elem.text.strip()
    return None


def read_artifacts_from_csv(
    csv_file_path: str,
) -> Tuple[List[Dict[str, str]], List[str]]:
    """
    Reads artifacts from a CSV file and returns a list of dictionaries and fieldnames.
    """
    artifacts = []
    fieldnames = []
    try:
        with open(csv_file_path, mode="r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            fieldnames = reader.fieldnames if reader.fieldnames else []
            for row in reader:
                # Ensure required fields are present
                if (
                    "group_id" in row
                    and "artifact_id" in row
                    and "start_version" in row
                ):
                    artifacts.append(row)
                else:
                    logging.warning(f"Missing fields in row: {row}")
    except FileNotFoundError:
        logging.error(f"CSV file not found: {csv_file_path}")
    except Exception as e:
        logging.error(f"Error reading CSV file: {e}")
    return artifacts, fieldnames


def process_artifact(artifact: Dict[str, str]) -> Dict[str, Any]:
    """
    Processes a single artifact to determine if it's hosted on GitHub or other SCM.
    Returns a new artifact dictionary with additional keys if applicable.
    """
    # Create a copy of the artifact to avoid modifying the original
    result_artifact = artifact.copy()
    group_id = artifact.get("group_id")
    artifact_id = artifact.get("artifact_id")
    version = artifact.get("start_version", "").strip()
    pom = get_pom(group_id, artifact_id, version)
    if pom:
        scm_url = get_scm_url_from_pom(pom)
        if scm_url:
            if "github.com" in scm_url:
                github_url = extract_github_url(scm_url)
                if github_url:
                    result_artifact["scm_url"] = scm_url
                    result_artifact["github_url"] = github_url
                    result_artifact["github_api_url"] = convert_github_url_to_api(
                        github_url
                    )
                    owner, repo = extract_owner_repo_from_github_url(github_url)
                    result_artifact["github_owner"] = owner
                    result_artifact["github_repo"] = repo
                else:
                    result_artifact["invalidGithubUrl"] = True
            else:
                # Non-GitHub SCM URL found
                result_artifact["scm_url"] = scm_url
                result_artifact["nonGithubLinkFound"] = True
        else:
            result_artifact["scmLinkNotFound"] = True
    else:
        result_artifact["pomNotFound"] = True
        result_artifact["scmLinkNotFound"] = (
            True  # Since no POM, SCM link is also not found
        )
    return result_artifact


def extract_github_url(scm_url: str) -> Optional[str]:
    """
    Extracts and standardizes the GitHub URL from the SCM URL.
    """
    # Pattern to match common GitHub URL structures and extract owner/repo
    pattern = re.compile(
        r"(?:github\.com[:/]|@github\.com[:/])([^/]+?)/([^/]+?)(?:\.git|/|$)"
    )
    match = pattern.search(scm_url)
    if match:
        owner, repo = match.groups()
        return f"https://github.com/{owner}/{repo}"
    else:
        logging.warning(f"Invalid GitHub URL structure in SCM URL: {scm_url}")
        return None


def extract_owner_repo_from_github_url(
    github_url: str,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Extracts the owner and repository name from a GitHub URL.

    Args:
        github_url (str): The GitHub URL.

    Returns:
        Tuple[Optional[str], Optional[str]]: A tuple containing the owner and repository name.
    """
    parsed_url = urlparse(github_url)
    if parsed_url.netloc not in ["github.com", "www.github.com"]:
        logging.warning(f"Invalid GitHub URL: {github_url}")
        return None, None

    path_parts = parsed_url.path.strip("/").split("/")

    if len(path_parts) >= 2:
        owner = path_parts[0]
        repo = path_parts[1].replace(".git", "")
        return owner, repo
    else:
        logging.warning(f"Invalid GitHub URL structure: {github_url}")
        return None, None


def convert_github_url_to_api(github_url):
    """
    Convert a standard GitHub URL to its corresponding GitHub API URL.

    Args:
        github_url (str): The GitHub URL to convert.

    Returns:
        str or None: The corresponding GitHub API URL, or None if the input URL is invalid.
    """
    # Parse the URL
    parsed_url = urlparse(github_url)

    # Ensure the URL is from github.com
    if parsed_url.netloc not in ["github.com", "www.github.com"]:
        logging.warning(f"Invalid GitHub URL: {github_url}")
        return None

    # Split the path and remove any trailing slash
    path = parsed_url.path.rstrip("/")

    # Remove .git suffix if present
    if path.endswith(".git"):
        path = path[:-4]

    # Split the path into components
    path_parts = path.strip("/").split("/")

    # The first two parts should be the owner and repo
    if len(path_parts) >= 2:
        owner = path_parts[0]
        repo = path_parts[1]
        # Initialize the base API URL
        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        return api_url
    else:
        logging.warning(f"Invalid GitHub URL structure: {github_url}")
        return None


def main():
    input_path = RQ2_1_INPUT
    output_csv = RQ2_1_OUTPUT
    filtered_output_csv = RQ2_1_FILTERED_OUTPUT  # File for artifacts with GitHub URLs
    non_github_output_csv = RQ2_1_NON_GITHUB_OUTPUT  # New file for non-GitHub SCM URLs

    artifacts, fieldnames = read_artifacts_from_csv(input_path)
    if not artifacts:
        logging.info("No artifacts to process.")
        return

    logging.info(f"Total artifacts to process: {len(artifacts)}")

    # Fieldnames for output CSV
    if not fieldnames:
        logging.error("No fieldnames found in input CSV.")
        return

    # Ensure all necessary fieldnames are included
    for field in [
        "scm_url",
        "github_url",
        "github_api_url",
        "github_owner",
        "github_repo",
    ]:
        if field not in fieldnames:
            fieldnames.append(field)

    pom_not_found_count = 0
    scm_link_not_found_count = 0
    github_link_not_found_count = 0
    non_github_link_found_count = 0
    successful_count = 0

    total_artifacts = len(artifacts)
    processed_count = 0
    start_time = time.time()

    try:
        with open(
            output_csv, mode="w", newline="", encoding="utf-8"
        ) as csvfile_all, open(
            filtered_output_csv, mode="w", newline="", encoding="utf-8"
        ) as csvfile_filtered, open(
            non_github_output_csv, mode="w", newline="", encoding="utf-8"
        ) as csvfile_non_github:
            # Initialize the CSV writers
            writer_all = csv.DictWriter(csvfile_all, fieldnames=fieldnames)
            writer_all.writeheader()

            writer_filtered = csv.DictWriter(csvfile_filtered, fieldnames=fieldnames)
            writer_filtered.writeheader()

            writer_non_github = csv.DictWriter(
                csvfile_non_github, fieldnames=fieldnames
            )
            writer_non_github.writeheader()

            # Use ThreadPoolExecutor for concurrent processing
            max_workers = min(10, total_artifacts)
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                future_to_artifact = {
                    executor.submit(process_artifact, artifact): artifact
                    for artifact in artifacts
                }
                for future in as_completed(future_to_artifact):
                    artifact = future_to_artifact[future]
                    try:
                        result = future.result()

                        # Remove temporary keys before writing
                        result_copy = result.copy()
                        result_copy.pop("pomNotFound", None)
                        result_copy.pop("scmLinkNotFound", None)
                        result_copy.pop("nonGithubLinkFound", None)
                        result_copy.pop("invalidGithubUrl", None)

                        # Write result to the main CSV
                        writer_all.writerow(result_copy)

                        # If artifact has a GitHub URL, write to the filtered CSV
                        if result.get("github_url"):
                            writer_filtered.writerow(result_copy)
                            successful_count += 1
                        elif result.get("nonGithubLinkFound"):
                            # Write artifacts with non-GitHub SCM URLs to the third CSV
                            writer_non_github.writerow(result_copy)
                            non_github_link_found_count += 1

                        processed_count += 1

                        # Print progress every 10 artifacts or at the end
                        if (
                            processed_count % 10 == 0
                            or processed_count == total_artifacts
                        ):
                            elapsed_time = time.time() - start_time
                            avg_time_per_artifact = elapsed_time / processed_count
                            remaining_artifacts = total_artifacts - processed_count
                            est_remaining_time = (
                                avg_time_per_artifact * remaining_artifacts
                            )
                            logging.info(
                                f"Processed {processed_count}/{total_artifacts} artifacts. "
                                f"Estimated time remaining: {est_remaining_time:.2f} seconds."
                            )

                        if result.get("pomNotFound"):
                            pom_not_found_count += 1
                        if result.get("scmLinkNotFound"):
                            scm_link_not_found_count += 1
                        if (
                            result.get("github_url") is None
                            and result.get("nonGithubLinkFound") is None
                        ):
                            github_link_not_found_count += 1

                    except Exception as e:
                        logging.error(f"Error processing artifact: {e}")
                        processed_count += 1
    except Exception as e:
        logging.error(f"Error writing to output CSV: {e}")

    # Output the counts
    logging.info(f"Total POM files that could not be found: {pom_not_found_count}")
    logging.info(f"Total SCM links that could not be found: {scm_link_not_found_count}")
    logging.info(
        f"Total GitHub links that could not be found: {github_link_not_found_count}"
    )
    logging.info(f"Total non-GitHub SCM links found: {non_github_link_found_count}")
    logging.info(
        f"Total artifacts successfully written with GitHub URLs: {successful_count}"
    )

    # Calculate and display the percentage of successful artifacts
    if total_artifacts > 0:
        success_percentage = (successful_count / total_artifacts) * 100
        logging.info(f"Success rate (GitHub URLs): {success_percentage:.2f}%")
    else:
        logging.info("No artifacts were processed.")

    logging.info(f"All artifacts have been written to {output_csv}")
    logging.info(
        f"Artifacts with GitHub URLs have been written to {filtered_output_csv}"
    )
    logging.info(
        f"Artifacts with non-GitHub SCM URLs have been written to {non_github_output_csv}"
    )


if __name__ == "__main__":
    main()
