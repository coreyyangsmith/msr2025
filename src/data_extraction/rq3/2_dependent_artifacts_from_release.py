import pandas as pd
import requests
import time
from tqdm import tqdm
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import threading


from src.classes.EnrichedRelease import EnrichedRelease
from src.utils.parsing import extract_combined_name_from_version_id
from src.utils.config import NEO4J_URL, MAX_WORKERS


"""
This script analyzes dependency relationships for affected software versions by querying a local GoblinWeaver API.
It performs the following tasks:


1. Reads a list of affected versions from rq3_1_affected_versions_list.csv
2. For each affected version:
   - Constructs and sends a Cypher query to the GoblinWeaver API to identify dependent artifacts (relationship_AR).
   - Processes the API response to extract details about dependent releases.
3. Aggregates the results and saves the data to a CSV file incrementally.
4. Logs progress statistics, including processing rate and estimated time remaining.


The script handles potential errors from the API and ensures intermediate results are saved for data integrity.
The script uses multithreading to improve performance when querying the API.
"""


# Constants for controlling concurrency
DEPENDENCY_WORKERS = MAX_WORKERS  # Use MAX_WORKERS from config
MAX_RETRIES = 2  # Maximum number of retries for API requests
BACKOFF_FACTOR = 2  # Exponential backoff factor
INITIAL_BACKOFF = 1  # Initial backoff in seconds


def process_release(row):
    parent_combined_name = row["parent_combined_name"]
    affected_versions = row["affected_version"].split(",")
    cve_id = row["cve_id"]

    for affected_version in affected_versions:
        affected_version = affected_version.strip()
        # Construct the release_id
        release_id = f"{parent_combined_name}:{affected_version}"

        # Added print statement for current active parent package and version
        print(
            f"Observing parent package: {parent_combined_name}, version: {affected_version}"
        )

        # Construct Cypher query
        query = f"""
        MATCH (parentRelease:Release {{id: "{release_id}"}})
        <-[:relationship_AR]-
        (parentArtifact:Artifact)
        MATCH (dependentRelease:Release)-[:dependency]->(parentArtifact)
        MATCH (dependentRelease)
        <-[:relationship_AR]-
        (dependentArtifact:Artifact)
        RETURN collect(DISTINCT dependentArtifact) as dependentArtifacts
        """

        backoff = INITIAL_BACKOFF

        while True:
            try:
                # Prepare request payload
                payload = {"statements": [{"statement": query}]}

                # Send request to Neo4j
                headers = {"Content-Type": "application/json"}
                response = requests.post(
                    NEO4J_URL,
                    auth=("neo4j", "password"),
                    headers=headers,
                    data=json.dumps(payload),
                    timeout=1200,  # Set a timeout for the request
                )

                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    sleep_time = int(retry_after) if retry_after else backoff
                    print(
                        f"Rate limited. Sleeping for {sleep_time} seconds before retrying..."
                    )
                    time.sleep(sleep_time)
                    backoff *= BACKOFF_FACTOR
                    continue  # Retry the request

                response.raise_for_status()

                # Process response
                results = response.json()
                print(results)
                if "results" in results and len(results["results"]) > 0:
                    result_set = results["results"][0]
                    data_entries = result_set.get("data", [])

                    if data_entries:
                        artifacts = []
                        for entry in data_entries:
                            row_data = entry.get("row", [])
                            if len(row_data) == 0 or not row_data[0]:
                                continue

                            # row_data[0] contains array of artifact objects
                            for artifact_obj in row_data[0]:
                                if not artifact_obj.get("found", False):
                                    continue

                                artifact_id = artifact_obj.get("id", "")
                                if not artifact_id:
                                    continue

                                # Split the id into group and artifact components
                                group_id, artifact_name = artifact_id.split(":", 1)

                                artifact_info = {
                                    "parent_combined_name": parent_combined_name,
                                    "dependentGroupId": group_id,
                                    "dependentArtifactId": artifact_name,
                                }
                                artifacts.append(artifact_info)

                        print(
                            f"Processed release {release_id}: found {len(artifacts)} dependencies."
                        )
                        return artifacts
                print(f"Invalid response for release {release_id}. Retrying...")
                time.sleep(backoff)
                backoff *= BACKOFF_FACTOR

            except requests.exceptions.RequestException as e:
                print(
                    f"Request exception for release {release_id}: {e}. Retrying in {backoff} seconds..."
                )
                time.sleep(backoff)
                backoff *= BACKOFF_FACTOR


def main():
    print("Starting the dependent artifacts extraction process...")

    # Read the affected versions data
    print("Reading affected versions from CSV...")
    df = pd.read_csv("data/rq3_1_affected_versions_list.csv")

    # Define CSV file path
    output_csv = "data/rq3_2_dependent_artifacts.csv"

    # Initialize CSV with headers
    header_written = False

    start_time = time.time()
    total_unique_pairs = 0
    processed_releases = 0
    failed_releases = 0

    # Create progress bar with enhanced statistics
    pbar = tqdm(
        total=len(df), desc="Processing Releases", unit="release", dynamic_ncols=True
    )

    # Initialize variables for statistics
    lock = threading.Lock()
    seen_pairs = set()

    print(f"Starting processing with {DEPENDENCY_WORKERS} workers...")

    # Process releases using thread pool with limited workers
    with ThreadPoolExecutor(max_workers=DEPENDENCY_WORKERS) as executor:
        # Submit all tasks
        future_to_row = {
            executor.submit(process_release, row): idx for idx, row in df.iterrows()
        }

        # Process completed tasks
        for future in as_completed(future_to_row):
            idx = future_to_row[future]
            try:
                batch_results = future.result()
                # Use lock to safely update shared variables
                with lock:
                    if batch_results:
                        unique_batch = []
                        for entry in batch_results:
                            pair = (
                                entry["parent_combined_name"],
                                entry["dependentGroupId"],
                                entry["dependentArtifactId"],
                            )
                            if pair not in seen_pairs:
                                seen_pairs.add(pair)
                                unique_batch.append(entry)

                        if unique_batch:
                            batch_df = pd.DataFrame(unique_batch)
                            if not header_written:
                                batch_df.to_csv(
                                    output_csv, mode="w", index=False, header=True
                                )
                                header_written = True
                                print(f"Wrote headers to {output_csv}.")
                            else:
                                batch_df.to_csv(
                                    output_csv, mode="a", index=False, header=False
                                )
                            total_unique_pairs += len(unique_batch)
                processed_releases += 1

                # Update progress bar with statistics
                elapsed_time = time.time() - start_time
                releases_per_second = (
                    processed_releases / elapsed_time if elapsed_time > 0 else 0
                )
                remaining_releases = len(df) - processed_releases
                eta_seconds = (
                    remaining_releases / releases_per_second
                    if releases_per_second > 0
                    else 0
                )
                eta = str(timedelta(seconds=int(eta_seconds)))

                pbar.set_postfix(
                    {
                        "Processed": f"{processed_releases}/{len(df)}",
                        "Unique Pairs": total_unique_pairs,
                        "Rate": f"{releases_per_second:.2f}/s",
                        "ETA": eta,
                    }
                )
                pbar.update(1)

            except Exception as e:
                with lock:
                    failed_releases += 1
                    processed_releases += 1
                    print(f"Error processing release at index {idx}: {e}")

                    elapsed_time = time.time() - start_time
                    releases_per_second = (
                        processed_releases / elapsed_time if elapsed_time > 0 else 0
                    )
                    remaining_releases = len(df) - processed_releases
                    eta_seconds = (
                        remaining_releases / releases_per_second
                        if releases_per_second > 0
                        else 0
                    )
                    eta = str(timedelta(seconds=int(eta_seconds)))

                    pbar.set_postfix(
                        {
                            "Processed": f"{processed_releases}/{len(df)}",
                            "Unique Pairs": total_unique_pairs,
                            "Rate": f"{releases_per_second:.2f}/s",
                            "ETA": eta,
                            "Failed": failed_releases,
                        }
                    )
                    pbar.update(1)

    pbar.close()

    print("\nProcessing complete.")
    print(f"Final results saved to {output_csv}")
    print(
        f"Found {total_unique_pairs} unique parent-dependent pairs across {len(df)} affected versions."
    )
    if failed_releases > 0:
        print(f"Failed to process {failed_releases} releases due to errors.")


if __name__ == "__main__":
    main()
