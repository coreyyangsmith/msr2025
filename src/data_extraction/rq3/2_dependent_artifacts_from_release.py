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
MAX_RETRIES = 5  # Maximum number of retries for API requests
BACKOFF_FACTOR = 2  # Exponential backoff factor
INITIAL_BACKOFF = 1  # Initial backoff in seconds


def process_release(row):
    parent_combined_name = row["parent_combined_name"]
    affected_version = row["affected_version"]
    cve_id = row["cve_id"]

    # Construct the release_id
    release_id = f"{parent_combined_name}:{affected_version}"

    # Construct Cypher query
    query = f"""
    MATCH (parentRelease:Release {{id: "{release_id}"}})
    <-[:relationship_AR]-
    (parentArtifact:Artifact)
    MATCH (dependentRelease:Release)-[:dependency]->(parentArtifact)
    RETURN parentArtifact, dependentRelease, parentRelease
    """

    attempt = 0
    backoff = INITIAL_BACKOFF

    while attempt < MAX_RETRIES:
        try:
            # Prepare request payload
            payload = {"statements": [{"statement": query}]}

            # Send request to Neo4j
            headers = {"Content-Type": "application/json"}
            response = requests.post(
                GOBLIN_API,
                auth=("neo4j", "password"),
                headers=headers,
                data=json.dumps(payload),
                timeout=30,  # Set a timeout for the request
            )

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                sleep_time = int(retry_after) if retry_after else backoff
                time.sleep(sleep_time)
                attempt += 1
                backoff *= BACKOFF_FACTOR
                continue  # Retry the request

            response.raise_for_status()

            # Process response
            results = response.json()

            if "results" in results and len(results["results"]) > 0:
                result_set = results["results"][0]
                data_entries = result_set.get("data", [])

                if data_entries:
                    batch_results = []
                    for entry in data_entries:
                        row_data = entry.get("row", [])

                        if len(row_data) < 2:
                            continue

                        # Get the dependent release data from row_data[1]
                        dependent_release = row_data[1]
                        dependent_id = dependent_release.get("id", "UNKNOWN")

                        # Split id into group_id:artifact_id:version
                        id_parts = dependent_id.split(":")
                        if len(id_parts) < 3:
                            continue

                        group_id, artifact_id, _ = id_parts[:3]

                        batch_results.append(
                            {
                                "parent_combined_name": parent_combined_name,
                                "dependentGroupId": group_id,
                                "dependentArtifactId": artifact_id,
                            }
                        )
                    return batch_results
            return []

        except requests.exceptions.RequestException:
            if attempt < MAX_RETRIES - 1:
                time.sleep(backoff)
                attempt += 1
                backoff *= BACKOFF_FACTOR
            else:
                return []

    return []


# Read the affected versions data
df = pd.read_csv("data/rq3_1_affected_versions_list.csv")


# Expand the affected versions into separate rows
df["affected_version"] = df["affected_version"].str.split(",")
df = df.explode("affected_version")


# Skip empty/null versions
df = df.dropna(subset=["affected_version"])
df = df[df["affected_version"].str.strip() != ""]


# GoblinWeaver API endpoint
GOBLIN_API = NEO4J_URL


# Define CSV file path
output_csv = "data/rq3_2_dependent_artifacts.csv"


# Initialize CSV with headers
header_written = False


start_time = time.time()
total_unique_pairs = 0
processed_releases = 0


# Create progress bar with enhanced statistics
pbar = tqdm(
    total=len(df), desc="Processing Releases", unit="release", dynamic_ncols=True
)


# Initialize variables for statistics
lock = threading.Lock()
seen_pairs = set()


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

        except Exception:
            with lock:
                processed_releases += 1
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


pbar.close()


print(f"\nFinal results saved to {output_csv}")
print(
    f"Found {total_unique_pairs} unique parent-dependent pairs across {len(df)} affected versions"
)
