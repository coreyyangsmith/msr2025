import csv
import logging
import re
import requests
import time
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
from datetime import datetime, timedelta

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple

from ...utils.config import (
    RQ2_10_INPUT,
    RQ2_10_OUTPUT,
    RQ2_10_FILTERED_OUTPUT,
    RQ2_10_NON_GITHUB_OUTPUT,
)
from ...utils.maven import get_pom_without_version
from ...utils.config import MAX_WORKERS
from ...utils.io import read_artifacts_from_csv_with_artifact
from ...utils.parsing import (
    get_scm_url_from_pom,
    extract_github_url,
    extract_owner_repo_from_github_url,
)
from ...utils.string_conversion import convert_github_url_to_api

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")


def process_artifact(artifact: Dict[str, str]) -> Dict[str, Any]:
    """
    Processes a single artifact to determine if it's hosted on GitHub or other SCM.
    Returns a new artifact dictionary with additional keys if applicable.
    """
    # Create a copy of the artifact to avoid modifying the original
    result_artifact = artifact.copy()

    # Split artifact string into group_id and artifact_id
    artifact_str = artifact.get("artifact", "")
    parts = artifact_str.split(":")
    if len(parts) >= 2:
        group_id = parts[0]
        artifact_id = parts[1]

        pom = get_pom_without_version(group_id, artifact_id)
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
            result_artifact["scmLinkNotFound"] = True
    else:
        result_artifact["invalidArtifactFormat"] = True
        result_artifact["pomNotFound"] = True
        result_artifact["scmLinkNotFound"] = True

    return result_artifact


def main():
    input_path = RQ2_10_INPUT
    output_csv = RQ2_10_OUTPUT
    filtered_output_csv = RQ2_10_FILTERED_OUTPUT
    non_github_output_csv = RQ2_10_NON_GITHUB_OUTPUT

    artifacts, fieldnames = read_artifacts_from_csv_with_artifact(input_path)
    if not artifacts:
        logging.info("No artifacts to process.")
        return

    # Ensure all necessary fieldnames are included
    for field in [
        "artifact",
        "scm_url",
        "github_url",
        "github_api_url",
        "github_owner",
        "github_repo",
    ]:
        if field not in fieldnames:
            fieldnames.append(field)

    results_all, results_filtered, results_non_github = [], [], []

    # Process artifacts with ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            executor.submit(process_artifact, artifact) for artifact in artifacts
        ]
        for idx, future in enumerate(as_completed(futures)):
            try:
                result = future.result()
                results_all.append(result)
                if result.get("github_url"):
                    results_filtered.append(result)
                elif result.get("nonGithubLinkFound"):
                    results_non_github.append(result)

                # Log progress every 100 artifacts
                if idx % 100 == 0:
                    logging.info(f"Processed {idx + 1}/{len(artifacts)} artifacts")

            except Exception as e:
                logging.error(f"Error processing artifact: {e}")

    # Write all results to CSVs at once
    with open(output_csv, mode="w", newline="", encoding="utf-8") as csvfile_all, open(
        filtered_output_csv, mode="w", newline="", encoding="utf-8"
    ) as csvfile_filtered, open(
        non_github_output_csv, mode="w", newline="", encoding="utf-8"
    ) as csvfile_non_github:
        writer_all = csv.DictWriter(csvfile_all, fieldnames=fieldnames)
        writer_all.writeheader()
        writer_all.writerows(results_all)

        writer_filtered = csv.DictWriter(csvfile_filtered, fieldnames=fieldnames)
        writer_filtered.writeheader()
        writer_filtered.writerows(results_filtered)

        writer_non_github = csv.DictWriter(csvfile_non_github, fieldnames=fieldnames)
        writer_non_github.writeheader()
        writer_non_github.writerows(results_non_github)

    logging.info("Processing complete.")


if __name__ == "__main__":
    main()
