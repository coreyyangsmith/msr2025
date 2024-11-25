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
DEPENDENCY_WORKERS = 10  # Limit workers to 10
MAX_CONNECTIONS = 10  # Limit concurrent connections

# Create connection semaphore
connection_semaphore = threading.Semaphore(MAX_CONNECTIONS)


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
    try:
        # Acquire connection semaphore
        with connection_semaphore:
            # Prepare request payload
            payload = {"statements": [{"statement": query}]}

            # Send request to Neo4j
            headers = {"Content-Type": "application/json"}
            response = requests.post(
                GOBLIN_API,
                auth=("neo4j", "Password1"),
                headers=headers,
                data=json.dumps(payload),
            )
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
                        dependent_timestamp = dependent_release.get("timestamp", None)

                        # Convert timestamp to date if it exists
                        if dependent_timestamp:
                            dependent_timestamp = datetime.fromtimestamp(
                                dependent_timestamp / 1000
                            ).strftime("%Y-%m-%d")

                        # Split id into group_id:artifact_id:version
                        id_parts = dependent_id.split(":")
                        if len(id_parts) < 3:
                            continue

                        group_id = id_parts[0]
                        artifact_id = id_parts[1]
                        version = id_parts[2]

                        batch_results.append(
                            {
                                "dependentGroupId": group_id,
                                "dependentArtifactId": artifact_id,
                                "dependentVersion": version,
                                "dependentTimestamp": dependent_timestamp,
                                "cve_id": cve_id,
                                "parent_combined_name": parent_combined_name,
                                "affected_version": affected_version,
                                "parent_release_id": release_id,
                            }
                        )
                    return batch_results
                return []
            else:
                print(f"No results found for release {release_id}")
                return []

            time.sleep(0.5)  # Increased delay to reduce API load

    except requests.exceptions.RequestException as e:
        print(f"Error querying {release_id}: {str(e)}")
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

# Initialize the CSV with headers
with open(output_csv, "w", newline="", encoding="utf-8") as f:
    f.write(
        "dependentGroupId,dependentArtifactId,dependentVersion,dependentTimestamp,cve_id,parent_combined_name,affected_version,parent_release_id\n"
    )

print(f"\nProcessing {len(df)} affected versions...")

start_time = time.time()
total_releases = 0
processed_releases = 0

# Create progress bar
pbar = tqdm(total=len(df), desc="Querying dependencies")

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

            if batch_results:
                batch_df = pd.DataFrame(batch_results)
                # Append to CSV without headers
                batch_df.to_csv(output_csv, mode="a", index=False, header=False)
                total_releases += len(batch_results)

            processed_releases += 1
            pbar.update(1)

            # Write progress update every 100 releases
            if processed_releases % 100 == 0 or processed_releases == len(df):
                # Calculate and display progress statistics
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

                print(f"\nProgress update:")
                print(f"Processed versions: {processed_releases}/{len(df)}")
                print(f"Total dependencies found: {total_releases}")
                if processed_releases > 0:
                    print(
                        f"Average dependencies per version: {total_releases/processed_releases:.2f}"
                    )
                print(f"Processing rate: {releases_per_second:.2f} versions/second")
                print(f"Estimated time remaining: {eta}")

        except Exception as e:
            print(f"Error processing version at index {idx}: {str(e)}")

pbar.close()

print(f"\nFinal results saved to {output_csv}")
print(f"Found {total_releases} dependent releases across {len(df)} affected versions")
