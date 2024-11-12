import pandas as pd
import requests
import xml.etree.ElementTree as ET
from tqdm import tqdm
import logging
import os
import time
from datetime import timedelta
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("rq3_extract_dependencies.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Global locks dictionary and its lock
locks = {}
locks_lock = threading.Lock()


def get_lock_for_file(output_path):
    with locks_lock:
        if output_path not in locks:
            locks[output_path] = threading.Lock()
        return locks[output_path]


def get_session_with_retries():
    session = requests.Session()
    retry_strategy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def process_version(
    version, target_dep, dependent_lib, output_folder, github_owner, github_repo
):
    """Process a single version and write results to output file if dependency is found"""
    group_id, artifact_id = target_dep.split(":")
    version_str = version["v"]
    pom_url = f"https://search.maven.org/remotecontent?filepath={group_id.replace('.','/')}/{artifact_id}/{version_str}/{artifact_id}-{version_str}.pom"

    session = get_session_with_retries()

    try:
        pom_response = session.get(pom_url, timeout=10)
        if pom_response.status_code == 200:
            # Parse POM XML
            root = ET.fromstring(pom_response.content)

            # Check if dependent library exists in dependencies
            dep_group_id, dep_artifact_id = dependent_lib.split(":")

            # Search in dependencies section
            namespaces = {"maven": "http://maven.apache.org/POM/4.0.0"}
            dependencies = root.findall(
                ".//maven:dependencies/maven:dependency", namespaces
            )

            for dep in dependencies:
                dep_group = dep.find("maven:groupId", namespaces)
                dep_artifact = dep.find("maven:artifactId", namespaces)
                dep_version = dep.find("maven:version", namespaces)

                if (
                    dep_group is not None
                    and dep_artifact is not None
                    and dep_group.text == dep_group_id
                    and dep_artifact.text == dep_artifact_id
                ):
                    logging.info(f"Found matching dependency in version {version_str}")

                    # Get release timestamp from version metadata
                    timestamp = version.get("timestamp", "")
                    release_timestamp = (
                        datetime.fromtimestamp(int(timestamp) / 1000).strftime(
                            "%Y-%m-%d"
                        )
                        if timestamp
                        else ""
                    )

                    # Get dependent library version
                    dependent_version = (
                        dep_version.text if dep_version is not None else ""
                    )

                    # Write result directly to file
                    output_path = os.path.join(
                        output_folder,
                        f"{github_owner}_{github_repo}/pom_dependencies.csv",
                    )
                    lock = get_lock_for_file(output_path)
                    with lock:
                        with open(output_path, "a") as f:
                            f.write(
                                f"{target_dep},{version_str},{dependent_lib},{dependent_version},{timestamp},{release_timestamp}\n"
                            )
                    return True

    except requests.exceptions.RequestException as e:
        logging.error(
            f"Network error processing POM for {target_dep} version {version_str}: {str(e)}"
        )
    except ET.ParseError as e:
        logging.error(
            f"XML parsing error for {target_dep} version {version_str}: {str(e)}"
        )
    except Exception as e:
        logging.error(
            f"Unexpected error processing POM for {target_dep} version {version_str}: {str(e)}"
        )

    return False


def process_dependency_pair(args):
    (
        row,
        output_folder,
        processed,
        total_pairs,
        start_time,
    ) = args

    parent = row["parent"]
    target_dep = row["dependent"]
    github_owner = row["github_owner"]
    github_repo = row["github_repo"]

    try:
        group_id, artifact_id = target_dep.split(":")
    except ValueError:
        logger.error(f"Invalid dependency format: {target_dep}")
        return

    # Calculate ETA
    elapsed_time = time.time() - start_time
    avg_time_per_pair = elapsed_time / processed if processed > 0 else 0
    remaining_pairs = total_pairs - processed
    eta_seconds = avg_time_per_pair * remaining_pairs
    eta = str(timedelta(seconds=int(eta_seconds)))

    logger.info(
        f"Processing dependency pair {processed}/{total_pairs}: {target_dep} (ETA: {eta})"
    )
    print(f"\nAnalyzing versions for {target_dep}... (ETA: {eta})")

    try:
        search_url = f"https://search.maven.org/solrsearch/select?q=g:{group_id}+AND+a:{artifact_id}&core=gav&rows=1000&wt=json"
        session = get_session_with_retries()
        response = session.get(search_url, timeout=10)
        response.raise_for_status()
        versions = response.json()["response"]["docs"]

        logger.info(f"Found {len(versions)} versions for {target_dep}")
        print(f"Found {len(versions)} versions to check...")

        # Process versions sequentially or with limited concurrency
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(
                    process_version,
                    version,
                    target_dep,
                    parent,
                    output_folder,
                    github_owner,
                    github_repo,
                )
                for version in versions
            ]

            for future in as_completed(futures):
                future.result()

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching versions for {target_dep}: {str(e)}")
        print(f"Failed to fetch versions for {target_dep}")
    except KeyError as e:
        logger.error(f"Error parsing versions for {target_dep}: {str(e)}")
        print(f"Error parsing versions for {target_dep}")
    except Exception as e:
        logger.error(f"Unexpected error for {target_dep}: {str(e)}")
        print(f"Unexpected error for {target_dep}")


def main():
    # Read the combined data
    df = pd.read_csv("data/rq3_4_combined.csv")

    output_folder = "data/rq2_opendigger"

    # Create output directory if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # For each unique github_owner/repo combination, create a CSV file with headers
    for _, row in df.iterrows():
        try:
            output_path = os.path.join(
                output_folder,
                f"{row['github_owner']}_{row['github_repo']}/pom_dependencies.csv",
            )
            # Create parent directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            if not os.path.exists(output_path):
                try:
                    with open(output_path, "w") as f:
                        f.write(
                            "target_dependency,target_version,dependent_library,dependent_version,release_timestamp,release_date\n"
                        )
                except IOError as e:
                    logger.error(f"Failed to write header to {output_path}: {str(e)}")
                    print(f"Error: Could not write to {output_path}")
                    continue
        except KeyError as e:
            logger.error(f"Missing required column in dataframe: {str(e)}")
            print(f"Error: Missing data for {str(e)}")
            continue
        except Exception as e:
            logger.error(f"Unexpected error processing row: {str(e)}")
            print(f"Error processing repository")
            continue

    total_pairs = len(df)
    processed = 0
    start_time = time.time()

    # Prepare arguments for dependency pairs
    args_list = []
    for _, row in df.iterrows():
        processed += 1
        args_list.append((row, output_folder, processed, total_pairs, start_time))

    # Process dependency pairs in parallel
    with ThreadPoolExecutor(max_workers=5) as executor:
        list(tqdm(executor.map(process_dependency_pair, args_list), total=total_pairs))

    # Calculate total execution time
    total_time = str(timedelta(seconds=int(time.time() - start_time)))

    logger.info(f"Completed extraction in {total_time}.")
    print(f"\nExtraction complete in {total_time}.")
    print(f"Results saved to {output_folder}")


if __name__ == "__main__":
    main()
