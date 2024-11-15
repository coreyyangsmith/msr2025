import pandas as pd
import requests
import xml.etree.ElementTree as ET
from tqdm import tqdm
import logging
import os
import time
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.utils.config import MAX_WORKERS

# Constants for controlling concurrency
MAX_WORKERS = MAX_WORKERS
VERSION_WORKERS = MAX_WORKERS / 2

thread_local = threading.local()
output_lock = threading.Lock()


def get_session():
    """Get a thread-local session object with retry strategy."""
    if not hasattr(thread_local, "session"):
        session = requests.Session()
        retries = Retry(
            total=5, backoff_factor=1, status_forcelist=[429, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        thread_local.session = session
    return thread_local.session


def process_version(version, target_dep, parent):
    """Process a single version and return result if dependency is found."""
    group_id, artifact_id = target_dep.split(":")
    version_str = version["v"]
    pom_url = f"https://search.maven.org/remotecontent?filepath={group_id.replace('.','/')}/{artifact_id}/{version_str}/{artifact_id}-{version_str}.pom"

    try:
        session = get_session()
        pom_response = session.get(pom_url)
        if pom_response.status_code == 200:
            # Parse POM XML
            root = ET.fromstring(pom_response.content)

            # Check if dependent library exists in dependencies
            parent_group_id, parent_artifact_id = parent.split(":")
            namespaces = {"maven": "http://maven.apache.org/POM/4.0.0"}
            dependencies = root.findall(
                ".//maven:dependencies/maven:dependency", namespaces
            )

            for dep in dependencies:
                dep_group = dep.find("maven:groupId", namespaces)
                dep_artifact = dep.find("maven:artifactId", namespaces)

                if (
                    dep_group is not None
                    and dep_artifact is not None
                    and dep_group.text == parent_group_id
                    and dep_artifact.text == parent_artifact_id
                ):
                    logging.info(
                        f"Found matching dependency in {target_dep} version {version_str}"
                    )
                    timestamp = version.get("timestamp", "")
                    release_date = time.strftime(
                        "%Y-%m-%d", time.localtime(timestamp / 1000)
                    )
                    return f"{target_dep},{parent},{version_str},{timestamp},{release_date}\n"
    except Exception as e:
        logging.error(
            f"Error processing POM for {target_dep} version {version_str}: {str(e)}"
        )
    return None


def process_dependency_pair(row):
    """Process a single dependency pair and return list of results."""
    results = []
    target_dep = row["dependent"]
    parent = row["parent"]
    try:
        group_id, artifact_id = target_dep.split(":")
    except ValueError:
        logging.error(f"Invalid dependency format: {target_dep}")
        return results  # Return empty results

    logging.info(f"Processing dependency pair: {target_dep}")
    try:
        session = get_session()
        search_url = f"https://search.maven.org/solrsearch/select?q=g:{group_id}+AND+a:{artifact_id}&core=gav&rows=1000&wt=json"  # confirm this URL
        response = session.get(search_url)
        versions = response.json()["response"]["docs"]
        logging.info(f"Found {len(versions)} versions for {target_dep}")

        with ThreadPoolExecutor(max_workers=VERSION_WORKERS) as executor:
            futures = [
                executor.submit(process_version, version, target_dep, parent)
                for version in versions
            ]
            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)
    except Exception as e:
        logging.error(f"Error fetching versions for {target_dep}: {str(e)}")
    return results


def extract_relevant_releases(input_path, output_path):
    """
    Extract releases where target dependency is found in POM file.

    Args:
        output_path: Path to save filtered releases data
    """

    # Import dependency pairs
    dependency_pairs_df = pd.read_csv(input_path)

    logging.info("Starting extraction of relevant releases...")
    print("Processing dependency pairs to find relevant releases...")

    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Create/overwrite output file with headers
    with open(output_path, "w") as f:
        f.write(
            "target_dependency,parent_artifact-group,dependent_version,dependent_release_timestamp,dependent_release_date\n"
        )

    total_pairs = len(dependency_pairs_df)
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for _, row in dependency_pairs_df.iterrows():
            futures.append(executor.submit(process_dependency_pair, row))

        for future in tqdm(as_completed(futures), total=total_pairs):
            results = future.result()
            if results:
                with output_lock:
                    with open(output_path, "a") as f:
                        f.writelines(results)

    total_time = str(timedelta(seconds=int(time.time() - start_time)))

    # Read final results to return DataFrame
    relevant_releases_df = pd.read_csv(output_path)

    logging.info(
        f"Completed extraction in {total_time}. Found {len(relevant_releases_df)} relevant releases."
    )
    print(
        f"\nExtraction complete in {total_time}. Found {len(relevant_releases_df)} relevant releases."
    )
    print(f"Results saved to {output_path}")

    return relevant_releases_df


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(threadName)s - %(message)s",
        handlers=[
            logging.FileHandler("rq3_extract_releases.log"),
            logging.StreamHandler(),
        ],
    )

    # Input and output paths
    input_path = "data/rq3_2_unique_dependents.csv"
    output_path = "data/rq3_3_relevant_releases.csv"

    # Run extraction
    extract_relevant_releases(input_path, output_path)
