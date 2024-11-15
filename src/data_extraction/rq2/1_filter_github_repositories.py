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
    RQ2_1_NON_GITHUB_OUTPUT,
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


def main():
    input_path = RQ2_1_INPUT
    output_csv = RQ2_1_OUTPUT  # all processed files rq_2_1_by_cve
    filtered_output_csv = RQ2_1_FILTERED_OUTPUT  # File for artifacts with GitHub URLs rq_2_1_by_cve_filtered
    non_github_output_csv = RQ2_1_NON_GITHUB_OUTPUT  # New file for non-GitHub SCM URLs rq_2_1_by_cve_non_github

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
            max_workers = min(MAX_WORKERS, total_artifacts)
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                future_to_artifact = {
                    executor.submit(
                        process_artifact, artifact
                    ): artifact  # process artifact
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
