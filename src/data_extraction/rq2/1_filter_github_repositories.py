import csv
import logging
import re
import requests
import time
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple
from functools import wraps

from ...utils.config import (
    RQ2_1_INPUT,
    RQ2_1_OUTPUT,
    RQ2_1_FILTERED_OUTPUT,
    RQ2_1_NON_GITHUB_OUTPUT,
    RQ2_1_FAILED_OUTPUT,  # New constant for failed artifacts output
)
from ...utils.maven import get_pom
from ...utils.config import MAX_WORKERS
from ...utils.io import read_artifacts_from_csv
from ...utils.parsing import (
    get_scm_url_from_pom,
    extract_github_url,
    extract_owner_repo_from_github_url,
)
from ...utils.string_conversion import convert_github_url_to_api

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Constants for rate limiting and retries
MAX_RETRIES = 5
BACKOFF_FACTOR = 1  # Base time in seconds
RATE_LIMIT_STATUS_CODES = [429]  # HTTP status code for Too Many Requests


def retry_with_backoff(max_retries=MAX_RETRIES, backoff_factor=BACKOFF_FACTOR):
    """
    Decorator for retrying a function with exponential backoff.
    """

    def retry_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.HTTPError as e:
                    status_code = e.response.status_code
                    if status_code in RATE_LIMIT_STATUS_CODES:
                        retries += 1
                        if retries > max_retries:
                            logging.error(
                                f"Max retries exceeded for function {func.__name__}"
                            )
                            raise
                        sleep_time = backoff_factor * (2 ** (retries - 1))
                        logging.warning(
                            f"Rate limit encountered. Sleeping for {sleep_time} seconds before retrying..."
                        )
                        time.sleep(sleep_time)
                    else:
                        raise
                except Exception as e:
                    retries += 1
                    if retries > max_retries:
                        logging.error(
                            f"Max retries exceeded for function {func.__name__}"
                        )
                        raise
                    sleep_time = backoff_factor * (2 ** (retries - 1))
                    logging.warning(
                        f"Error encountered: {e}. Retrying in {sleep_time} seconds..."
                    )
                    time.sleep(sleep_time)

        return wrapper

    return retry_decorator


@retry_with_backoff()
def safe_get_pom(group_id: str, artifact_id: str, version: str):
    """
    Wrapper around get_pom with retry logic.
    """
    return get_pom(group_id, artifact_id, version)


def process_artifact(artifact: Dict[str, str]) -> Dict[str, Any]:
    """
    Processes a single artifact to determine if it's hosted on GitHub or other SCM.
    Returns a new artifact dictionary with additional keys if applicable.
    """
    result_artifact = artifact.copy()
    group_id = artifact.get("group_id")
    artifact_id = artifact.get("artifact_id")
    version = artifact.get("start_version", "").strip()

    try:
        pom = safe_get_pom(group_id, artifact_id, version)
    except Exception as e:
        logging.error(f"Failed to get POM for {group_id}:{artifact_id}:{version}: {e}")
        pom = None
        # Include the error message in the result artifact
        result_artifact["processing_error"] = str(e)

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


def main():
    input_path = RQ2_1_INPUT
    output_csv = RQ2_1_OUTPUT
    filtered_output_csv = RQ2_1_FILTERED_OUTPUT
    non_github_output_csv = RQ2_1_NON_GITHUB_OUTPUT
    failed_output_csv = RQ2_1_FAILED_OUTPUT  # New CSV file for failed artifacts

    artifacts, fieldnames = read_artifacts_from_csv(input_path)
    if not artifacts:
        logging.info("No artifacts to process.")
        return

    logging.info(f"Total artifacts to process: {len(artifacts)}")

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
        "processing_error",  # New field for error messages
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

    # Adjust MAX_WORKERS to control the rate of API requests
    max_workers = min(
        MAX_WORKERS, total_artifacts, 10
    )  # Limit to 10 to prevent rate limiting

    failed_artifacts = []

    try:
        with (
            open(output_csv, mode="w", newline="", encoding="utf-8") as csvfile_all,
            open(
                filtered_output_csv, mode="w", newline="", encoding="utf-8"
            ) as csvfile_filtered,
            open(
                non_github_output_csv, mode="w", newline="", encoding="utf-8"
            ) as csvfile_non_github,
            open(
                failed_output_csv, mode="w", newline="", encoding="utf-8"
            ) as csvfile_failed,
        ):  # Open the failed artifacts CSV file
            # Initialize the CSV writers
            writer_all = csv.DictWriter(csvfile_all, fieldnames=fieldnames)
            writer_all.writeheader()

            writer_filtered = csv.DictWriter(csvfile_filtered, fieldnames=fieldnames)
            writer_filtered.writeheader()

            writer_non_github = csv.DictWriter(
                csvfile_non_github, fieldnames=fieldnames
            )
            writer_non_github.writeheader()

            writer_failed = csv.DictWriter(csvfile_failed, fieldnames=fieldnames)
            writer_failed.writeheader()

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
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
                        elif result.get("processing_error"):
                            # Write failed artifacts to the failed CSV
                            writer_failed.writerow(result_copy)
                            failed_artifacts.append(result_copy)
                        else:
                            # Artifacts that didn't fit in any category
                            github_link_not_found_count += 1

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

                    except Exception as e:
                        logging.error(f"Error processing artifact {artifact}: {e}")
                        processed_count += 1
                        # Include the error message in the artifact
                        artifact["processing_error"] = str(e)
                        # Write failed artifact to the failed CSV
                        writer_failed.writerow(artifact)
                        failed_artifacts.append(artifact)
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
    logging.info(f"Total artifacts failed to process: {len(failed_artifacts)}")

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
    logging.info(f"Failed artifacts have been written to {failed_output_csv}")


if __name__ == "__main__":
    main()
