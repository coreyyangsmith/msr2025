import pandas as pd
import requests
import xml.etree.ElementTree as ET
from tqdm import tqdm
import logging
import os
import time
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed


def process_version(version, target_dep, dependent_lib, output_path):
    """Process a single version and write results to output file if dependency is found"""
    group_id, artifact_id = target_dep.split(":")
    version_str = version["v"]
    pom_url = f"https://search.maven.org/remotecontent?filepath={group_id.replace('.','/')}/{artifact_id}/{version_str}/{artifact_id}-{version_str}.pom"

    try:
        pom_response = requests.get(pom_url)
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

                if (
                    dep_group is not None
                    and dep_artifact is not None
                    and dep_group.text == dep_group_id
                    and dep_artifact.text == dep_artifact_id
                ):
                    logging.info(f"Found matching dependency in version {version_str}")
                    # Write result directly to file
                    with open(output_path, "a") as f:
                        f.write(
                            f"{target_dep},{dependent_lib},{version_str},{version['timestamp']}\n"
                        )
                    return True

    except Exception as e:
        logging.error(
            f"Error processing POM for {target_dep} version {version_str}: {str(e)}"
        )
        print(f"Error processing POM for version {version_str}")

    return False


def process_dependency_pair(row, output_path, processed, total_pairs, start_time):
    """Process a single dependency pair and all its versions"""
    parent = row["parent"]
    target_dep = row["dependent"]
    try:
        group_id, artifact_id = target_dep.split(":")
    except ValueError:
        logging.error(f"Invalid dependency format: {target_dep}")
        return

    # Calculate ETA
    elapsed_time = time.time() - start_time
    avg_time_per_pair = elapsed_time / processed
    remaining_pairs = total_pairs - processed
    eta_seconds = avg_time_per_pair * remaining_pairs
    eta = str(timedelta(seconds=int(eta_seconds)))

    logging.info(
        f"Processing dependency pair {processed}/{total_pairs}: {target_dep} (ETA: {eta})"
    )
    print(f"\nAnalyzing versions for {target_dep}... (ETA: {eta})")

    try:
        search_url = f"https://search.maven.org/solrsearch/select?q=g:{group_id}+AND+a:{artifact_id}&core=gav&rows=1000&wt=json"
        response = requests.get(search_url)
        versions = response.json()["response"]["docs"]

        logging.info(f"Found {len(versions)} versions for {target_dep}")
        print(f"Found {len(versions)} versions to check...")

        # Process versions in parallel with ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=12) as executor:
            futures = [
                executor.submit(
                    process_version, version, target_dep, parent, output_path
                )
                for version in versions
            ]

            # Wait for all futures to complete
            for future in as_completed(futures):
                future.result()  # Get result to propagate any exceptions

    except Exception as e:
        logging.error(f"Error fetching versions for {target_dep}: {str(e)}")
        print(f"Failed to fetch versions for {target_dep}")


def extract_relevant_releases(input_path, output_path):
    """
    Extract releases where target dependency is found in POM file

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
            "target_dependency,dependent_library,version,release_timestamp,release_date\n"
        )

    total_pairs = len(dependency_pairs_df)
    processed = 0
    start_time = time.time()

    # Process each dependency pair
    for _, row in tqdm(dependency_pairs_df.iterrows(), total=total_pairs):
        processed += 1
        process_dependency_pair(row, output_path, processed, total_pairs, start_time)

    # Calculate total execution time
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
        format="%(asctime)s - %(levelname)s - %(message)s",
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
