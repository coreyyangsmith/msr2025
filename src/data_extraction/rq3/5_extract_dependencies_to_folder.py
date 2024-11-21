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

"""
This script extracts Maven dependency data for specified dependency pairs by processing Maven POM files.

### Steps:
1. Reads a CSV file (`rq3_4_combined.csv`) containing enriched dependency pairs with GitHub repository information.
2. For each dependency pair:
   - Queries Maven Central to fetch all versions of the dependent artifact.
   - Checks the POM file for each version to identify if it references the parent dependency.
   - If a match is found, extracts the dependency version, release timestamp, and release date.
   - Saves the results into a CSV file organized by GitHub owner/repo (one file per repository).
3. Uses concurrent processing to handle multiple dependency pairs and artifact versions in parallel.

### Outputs:
- Results are saved in a structured folder under `data/rq2_opendigger/`, with one CSV file per GitHub repository.
- Each CSV contains columns:
  - `target_dependency`
  - `target_version`
  - `dependent_library`
  - `dependent_version`
  - `release_timestamp`
  - `release_date`

### Logging:
- Logs are saved to `rq3_extract_dependencies.log` and streamed to the console.

### Dependencies:
- pandas
- requests
- xml.etree.ElementTree
- concurrent.futures
- threading
- tqdm
- logging
- urllib3 (for HTTP retries)

### Functions:
- `get_session_with_retries()`: Returns a session with retry logic for robust HTTP requests.
- `process_version()`: Processes a single artifact version and extracts dependency data.
- `process_dependency_pair()`: Handles all versions of a dependency pair, delegating work to `process_version`.
- `main()`: Orchestrates the workflow, initializes logging, and manages dependencies and outputs.

### Usage:
- Ensure the input file `rq3_4_combined.csv` exists in the `data/` directory.
- Run the script as a standalone program to extract and save dependency data.

### Notes:
- The script uses a thread-safe locking mechanism to avoid conflicts while writing to shared files.
- Customize `MAX_WORKERS` to adjust concurrency based on available system resources.

"""


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

MAX_WORKERS = 24  # Set max workers to 24 as per your request


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
        print(f"Fetching POM for {target_dep} version {version_str}...")
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
                    print(
                        f"Found matching dependency in {target_dep} version {version_str}"
                    )

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
        else:
            logging.warning(
                f"Failed to fetch POM for {target_dep} version {version_str}: HTTP {pom_response.status_code}"
            )
            print(
                f"Failed to fetch POM for {target_dep} version {version_str}: HTTP {pom_response.status_code}"
            )

    except requests.exceptions.RequestException as e:
        logging.error(
            f"Network error processing POM for {target_dep} version {version_str}: {str(e)}"
        )
        print(
            f"Network error processing POM for {target_dep} version {version_str}: {str(e)}"
        )
    except ET.ParseError as e:
        logging.error(
            f"XML parsing error for {target_dep} version {version_str}: {str(e)}"
        )
        print(f"XML parsing error for {target_dep} version {version_str}: {str(e)}")
    except Exception as e:
        logging.error(
            f"Unexpected error processing POM for {target_dep} version {version_str}: {str(e)}"
        )
        print(
            f"Unexpected error processing POM for {target_dep} version {version_str}: {str(e)}"
        )

    return False


def process_dependency_pair(args):
    row, output_folder = args

    parent = row["parent"]
    target_dep = row["dependent"]
    github_owner = row["github_owner"]
    github_repo = row["github_repo"]

    try:
        group_id, artifact_id = target_dep.split(":")
    except ValueError:
        logger.error(f"Invalid dependency format: {target_dep}")
        print(f"Invalid dependency format: {target_dep}")
        return

    print(f"\nProcessing dependency pair: {target_dep}")

    try:
        search_url = f"https://search.maven.org/solrsearch/select?q=g:{group_id}+AND+a:{artifact_id}&core=gav&rows=1000&wt=json"
        session = get_session_with_retries()
        print(f"Fetching versions for {target_dep}...")
        response = session.get(search_url, timeout=10)
        response.raise_for_status()
        versions = response.json()["response"]["docs"]

        logger.info(f"Found {len(versions)} versions for {target_dep}")
        print(f"Found {len(versions)} versions for {target_dep}")

        # Process versions in parallel
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
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
                try:
                    future.result()
                except Exception as e:
                    logging.error(f"Error in processing version: {str(e)}")
                    print(f"Error in processing version: {str(e)}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching versions for {target_dep}: {str(e)}")
        print(f"Network error fetching versions for {target_dep}: {str(e)}")
    except KeyError as e:
        logger.error(f"Error parsing versions for {target_dep}: {str(e)}")
        print(f"Error parsing versions for {target_dep}: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error for {target_dep}: {str(e)}")
        print(f"Unexpected error for {target_dep}: {str(e)}")


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

    start_time = time.time()

    # Prepare arguments for dependency pairs
    args_list = []
    for row in df.to_dict("records"):
        print(f"row: {row}")
        print(f"output_folder: {output_folder}")
        args_list.append((row, output_folder))

    total_pairs = len(args_list)

    # Process dependency pairs in parallel
    print(
        f"Starting to process {total_pairs} dependency pairs with {MAX_WORKERS} workers..."
    )
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        list(tqdm(executor.map(process_dependency_pair, args_list), total=total_pairs))

    # Calculate total execution time
    total_time = str(timedelta(seconds=int(time.time() - start_time)))

    logger.info(f"Completed extraction in {total_time}.")
    print(f"\nExtraction complete in {total_time}.")
    print(f"Results saved to {output_folder}")


if __name__ == "__main__":
    main()
