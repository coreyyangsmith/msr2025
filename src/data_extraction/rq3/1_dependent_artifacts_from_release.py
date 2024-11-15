import pandas as pd
import requests
import time
from tqdm import tqdm
from datetime import datetime, timedelta  # Import timedelta explicitly

from src.classes.EnrichedRelease import EnrichedRelease
from src.utils.parsing import extract_combined_name_from_version_id

# Read the enriched data from RQ2
df = pd.read_csv("data/rq2_8_enriched.csv")

# Get unique patched release IDs where cve_patched is True
patched_releases = df[df["cve_patched"] == True]["patched_release_id"].unique()

# Initialize empty DataFrame with required columns
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
GOBLIN_API = "http://localhost:8080/cypher"

print(f"\nProcessing {len(patched_releases)} patched releases...")

start_time = time.time()
total_releases = 0

# Process each release with progress bar
for idx, release_id in enumerate(tqdm(patched_releases, desc="Querying dependencies")):
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
            continue

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

        if batch_results:
            batch_df = pd.DataFrame(batch_results)
            results_df = pd.concat([results_df, batch_df], ignore_index=True)
            total_releases += len(batch_results)

            # Write intermediate results every 100 releases or at the end
            if (idx + 1) % 100 == 0 or idx == len(patched_releases) - 1:
                results_df.to_csv("data/rq3_1_dependent_artifacts.csv", index=False)

                # Calculate and display progress statistics
                elapsed_time = time.time() - start_time
                releases_per_second = (idx + 1) / elapsed_time
                remaining_releases = len(patched_releases) - (idx + 1)
                eta_seconds = (
                    remaining_releases / releases_per_second
                    if releases_per_second > 0
                    else 0
                )
                eta = str(timedelta(seconds=int(eta_seconds)))

                print(f"\nProgress update:")
                print(f"Processed releases: {idx + 1}/{len(patched_releases)}")
                print(f"Total releases found: {total_releases}")
                print(f"Average releasts per artifact: {total_releases/(idx + 1):.2f}")
                print(f"Processing rate: {releases_per_second:.2f} releases/second")
                print(f"Estimated time remaining: {eta}")

        # Add small delay to avoid overwhelming the API
        time.sleep(0.1)

    except requests.exceptions.RequestException as e:
        print(f"Error querying {release_id}: {str(e)}")
        continue

print(f"\nFinal results saved to data/rq3_1_dependent_artifacts.csv")
print(
    f"Found {total_releases} dependent releases across {len(patched_releases)} releases"
)
