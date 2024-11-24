import pandas as pd
import requests
import time
from tqdm import tqdm
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.classes.EnrichedRelease import EnrichedRelease
from src.utils.parsing import extract_combined_name_from_version_id
from src.utils.config import NEO4J_URL, MAX_WORKERS

"""
This script analyzes dependency relationships for software releases by querying a local GoblinWeaver API.
It performs the following tasks:

1. Reads an enriched dataset of patched releases from a CSV file.
2. Filters unique release IDs marked as patched (`cve_patched` is True).
3. For each patched release:
   - Constructs and sends a Cypher query to the GoblinWeaver API to identify dependent artifacts (relationship_AR).
   - Processes the API response to extract details about dependent releases.
4. Aggregates the results into a pandas DataFrame and saves the data to a CSV file at regular intervals.
5. Logs progress statistics, including processing rate and estimated time remaining.

The script handles potential errors from the API and ensures intermediate results are saved for data integrity.
The script uses multithreading to improve performance when querying the API.

Dependencies:
- pandas
- requests
- tqdm
- EnrichedRelease class from `src.classes.EnrichedRelease`
- `extract_combined_name_from_version_id` function from `src.utils.parsing`

Usage:
Run the script in an environment where the GoblinWeaver API is accessible, and the input data file is present at `data/rq2_8_enriched.csv`.
"""


def process_release(row):
    # Ensure required keys are present
    required_keys = ["combined_name", "end_version"]
    for key in required_keys:
        if key not in row:
            raise ValueError(f"Missing required key: {key}")

    # Construct the release_id
    release_id = f"{row['combined_name']}:{row['end_version']}"

    # Construct Cypher query
    query = f"""
    MATCH (parentRelease:Release {{id: "{release_id}"}})
    <-[:relationship_AR]-
    (parentArtifact:Artifact)
    MATCH (dependentRelease:Release)-[:dependency]->(parentArtifact)
    RETURN parentArtifact, dependentRelease, parentRelease
    """

    try:
        # Make API request with updated payload structure
        payload = {"query": query, "addedValues": []}
        response = requests.post(GOBLIN_API, json=payload)
        response.raise_for_status()

        results = response.json()
        # Debugging: Check the type and content of the response
        if isinstance(results, dict):
            data = results.get("nodes", [])
        elif isinstance(results, list):
            data = results
        else:
            print(f"Unexpected API response format for release {release_id}: {results}")
            return []

        # Process results
        batch_results = []
        for result in data:
            if not isinstance(result, dict):
                print(f"Unexpected result format: {result}")
                continue
            dependent_release = EnrichedRelease(result)
            parent_combined_name = extract_combined_name_from_version_id(release_id)
            batch_results.append(
                {
                    "parent_release_id": release_id,
                    "parent_combined_name": parent_combined_name,
                    "dependent_id": dependent_release.id,
                    "dependent_combined_name": dependent_release.combined_name,
                    "dependent_version": dependent_release.release_version,
                    "dependent_timestamp": dependent_release.release_timestamp,
                    "dependent_date": dependent_release.release_date,
                }
            )

        time.sleep(0.1)  # Small delay to avoid overwhelming the API
        return batch_results

    except requests.exceptions.RequestException as e:
        print(f"Error querying {release_id}: {str(e)}")
        return []


# Read the enriched data from RQ2
df = pd.read_csv("data/rq0_4_unique_cves.csv")
cves = df[df["cve_patched"]]
print(cves)

results_df = pd.DataFrame(
    columns=[
        "parent_release_id",
        "parent_combined_name",
        "dependent_id",
        "dependent_combined_name",
        "dependent_version",
        "dependent_timestamp",
        "dependent_date",
    ]
)

# GoblinWeaver API endpoint
GOBLIN_API = NEO4J_URL

print(f"\nProcessing {len(cves)} patched releases...")

start_time = time.time()
total_releases = 0
processed_releases = 0

# Create progress bar
pbar = tqdm(total=len(cves), desc="Querying dependencies")

# Process releases using thread pool
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    # Submit all tasks
    future_to_row = {
        executor.submit(process_release, row): idx for idx, row in cves.iterrows()
    }

    # Process completed tasks
    for future in as_completed(future_to_row):
        idx = future_to_row[future]
        try:
            batch_results = future.result()

            if batch_results:
                batch_df = pd.DataFrame(batch_results)
                results_df = pd.concat([results_df, batch_df], ignore_index=True)
                total_releases += len(batch_results)

            processed_releases += 1
            pbar.update(1)

            # Write intermediate results every 100 releases or at the end
            if processed_releases % 100 == 0 or processed_releases == len(cves):
                results_df.to_csv("data/rq3_1_dependent_artifacts.csv", index=False)

                # Calculate and display progress statistics
                elapsed_time = time.time() - start_time
                releases_per_second = processed_releases / elapsed_time
                remaining_releases = len(cves) - processed_releases
                eta_seconds = (
                    remaining_releases / releases_per_second
                    if releases_per_second > 0
                    else 0
                )
                eta = str(timedelta(seconds=int(eta_seconds)))

                print(f"\nProgress update:")
                print(f"Processed releases: {processed_releases}/{len(cves)}")
                print(f"Total releases found: {total_releases}")
                print(
                    f"Average releases per artifact: {total_releases/processed_releases:.2f}"
                )
                print(f"Processing rate: {releases_per_second:.2f} releases/second")
                print(f"Estimated time remaining: {eta}")

        except Exception as e:
            print(f"Error processing release at index {idx}: {str(e)}")

pbar.close()

print(f"\nFinal results saved to data/rq3_1_dependent_artifacts.csv")
print(f"Found {total_releases} dependent releases across {len(cves)} releases")
