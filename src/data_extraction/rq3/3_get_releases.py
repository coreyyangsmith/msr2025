import pandas as pd
import requests
import json
import time
from datetime import datetime
from tqdm import tqdm
import concurrent.futures
<<<<<<< HEAD
from packaging import version
=======
>>>>>>> 7156b850314cd75923fd946c9ded4e961f904662
from src.utils.config import NEO4J_URL, NEO4J_AUTH, MAX_WORKERS

"""
This script analyzes the dependency relationships between artifacts and their releases by querying a local GoblinWeaver API.
It performs the following tasks:

1. Reads the dependency relationships from rq3_2_dependent_artifacts.csv
2. For each parent-dependent pair:
   - Queries Neo4j to get release information about the dependency relationship
   - Extracts release versions, timestamps, and dependency versions
<<<<<<< HEAD
   - Keeps only the highest version within affected versions
=======
>>>>>>> 7156b850314cd75923fd946c9ded4e961f904662
3. Continuously saves the enriched dependency data to a CSV file
4. Handles API rate limiting and errors with retries and backoff
"""

# Constants
MAX_RETRIES = 3
INITIAL_BACKOFF = 1
BACKOFF_FACTOR = 2
OUTPUT_FILE = "data/rq3_3_release_dependencies.csv"


def query_neo4j(parent_artifact_id, dependent_artifact_id):
    """Query Neo4j for release information about a dependency relationship"""
    print(f"[Query] {parent_artifact_id} -> {dependent_artifact_id}")

    query = f"""
    MATCH (parentArtifact:Artifact {{id: "{parent_artifact_id}"}})
    MATCH (dependentArtifact:Artifact {{id: "{dependent_artifact_id}"}})
    MATCH (dependentRelease:Release)<-[:relationship_AR]-(dependentArtifact)
    MATCH (dependencyRelease)-[d:dependency]->(parentArtifact)
    RETURN
      dependentArtifact.id AS dependentArtifactId,
      dependentRelease.version AS dependentReleaseVersion,
      dependentRelease.timestamp AS dependentReleaseTimestamp,
      d.targetVersion AS parentReleaseVersion,
      parentArtifact.id AS parentArtifactId
    """

    payload = {"statements": [{"statement": query}]}
    headers = {"Content-Type": "application/json"}

    backoff = INITIAL_BACKOFF
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                NEO4J_URL,
                auth=NEO4J_AUTH,
                headers=headers,
                data=json.dumps(payload),
                timeout=120,
            )

            if response.status_code == 429:  # Rate limited
                print(f"[Rate limit] Backing off {backoff}s")
                time.sleep(backoff)
                backoff *= BACKOFF_FACTOR
                continue

            response.raise_for_status()
            return response.json()

        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                print(f"[Error] Failed after {MAX_RETRIES} attempts: {str(e)}")
                return None
            print(f"[Retry] Attempt {attempt + 1} failed, backing off {backoff}s")
            time.sleep(backoff)
            backoff *= BACKOFF_FACTOR

    return None


def process_dependency_pair(row):
    """Process a single parent-dependent artifact pair"""
    parent_id = row["parent_combined_name"]
    dependent_id = f"{row['dependentGroupId']}:{row['dependentArtifactId']}"
    patched_version = row["patched_version"]
    affected_versions = row["affected_versions"].split(",")

    result = query_neo4j(parent_id, dependent_id)
    if not result or "results" not in result or not result["results"][0]["data"]:
        return None

    releases_affected = {}
    releases_patched = {}

    for record in result["results"][0]["data"]:
        record_row = record["row"]
        dep_id = record_row[0]  # This is now just the group_id:artifact_id
        dep_version = record_row[1]
        timestamp = record_row[2]
        parent_version = record_row[3]
        parent_artifact_id = record_row[4]

        # Case 1: Highest dependent_version for highest parent_version in affected_versions
        if parent_version in affected_versions:
            try:
                parsed_parent_version = version.parse(parent_version)
                parsed_dep_version = version.parse(dep_version)
            except version.InvalidVersion:
                print(
                    f"[Warning] Invalid version format for parent_version '{parent_version}' or dependent_version '{dep_version}'. Skipping affected version."
                )
                continue

            if dep_id not in releases_affected:
                releases_affected[dep_id] = {
                    "version": dep_version,
                    "parsed_version": parsed_dep_version,
                    "parent_version": parsed_parent_version,
                    "parent_id": parent_artifact_id,
                    "timestamp": timestamp,
                }
            else:
                existing = releases_affected[dep_id]
                if parsed_parent_version > existing["parent_version"]:
                    releases_affected[dep_id] = {
                        "version": dep_version,
                        "parsed_version": parsed_dep_version,
                        "parent_version": parsed_parent_version,
                        "parent_id": parent_artifact_id,
                        "timestamp": timestamp,
                    }
                elif parsed_parent_version == existing["parent_version"]:
                    if parsed_dep_version > existing["parsed_version"]:
                        releases_affected[dep_id] = {
                            "version": dep_version,
                            "parsed_version": parsed_dep_version,
                            "parent_version": parsed_parent_version,
                            "parent_id": parent_artifact_id,
                            "timestamp": timestamp,
                        }

        # Case 2: Lowest dependent_version for parent_version >= patched_version
        try:
            parsed_patched_version = version.parse(patched_version)
            parsed_parent_version = version.parse(parent_version)
            parsed_dep_version = version.parse(dep_version)
        except version.InvalidVersion:
            print(
                f"[Warning] Invalid version format for patched_version '{patched_version}', parent_version '{parent_version}', or dependent_version '{dep_version}'. Skipping patched version."
            )
            continue

        if parsed_parent_version >= parsed_patched_version:
            if dep_id not in releases_patched:
                releases_patched[dep_id] = {
                    "version": dep_version,
                    "parsed_version": parsed_dep_version,
                    "parent_version": parsed_parent_version,
                    "parent_id": parent_artifact_id,
                    "timestamp": timestamp,
                }
            else:
                existing = releases_patched[dep_id]
                if parsed_dep_version < existing["parsed_version"]:
                    releases_patched[dep_id] = {
                        "version": dep_version,
                        "parsed_version": parsed_dep_version,
                        "parent_version": parsed_parent_version,
                        "parent_id": parent_artifact_id,
                        "timestamp": timestamp,
                    }

    # Combine affected and patched releases
    releases = []

    for dep_id, affected in releases_affected.items():
        timestamp = affected["timestamp"]
        release_date = datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d")

        releases.append(
            {
                "parent_artifact_id": affected["parent_id"],
                "parent_version": str(affected["parent_version"]),
                "dependent_artifact_id": dep_id,
                "dependent_version": affected["version"],
                "dependent_timestamp": timestamp,
                "dependent_date": release_date,
                "type": "affected",
            }
        )

    for dep_id, patched in releases_patched.items():
        timestamp = patched["timestamp"]
        release_date = datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d")

        releases.append(
            {
                "parent_artifact_id": patched["parent_id"],
                "parent_version": str(patched["parent_version"]),
                "dependent_artifact_id": dep_id,
                "dependent_version": patched["version"],
                "dependent_timestamp": timestamp,
                "dependent_date": release_date,
                "type": "patched",
            }
        )

    return releases if releases else None


def write_batch_to_csv(results, first_write=False):
    """Write a batch of results to CSV"""
    if not results:
        return

    df = pd.DataFrame(results)
    mode = "w" if first_write else "a"
    header = first_write
    df.to_csv(OUTPUT_FILE, mode=mode, header=header, index=False)


def main():
    print("[Start] Release Dependency Analysis")
    df = pd.read_csv("data/rq3_2_dependent_artifacts.csv")
    print(f"[Load] {len(df)} dependency relationships")

    start_time = datetime.now()
    results_buffer = []
    processed_count = 0
    error_count = 0
    first_write = True

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_row = {
            executor.submit(process_dependency_pair, row): row
            for _, row in df.iterrows()
        }

        for future in tqdm(
            concurrent.futures.as_completed(future_to_row),
            total=len(df),
            desc="Processing",
            unit="pairs",
        ):
            processed_count += 1
            try:
                releases = future.result()
                if releases:
                    results_buffer.extend(releases)

                # Write to CSV every 100 releases or when buffer exceeds 1000 items
                if len(results_buffer) >= 1000 or (
                    releases and processed_count % 100 == 0
                ):
                    write_batch_to_csv(results_buffer, first_write)
                    first_write = False
                    results_buffer = []

                # Log progress every 5 items
                if processed_count % 5 == 0:
                    elapsed_time = datetime.now() - start_time
                    avg_time = elapsed_time / processed_count
                    remaining = len(df) - processed_count
                    eta = datetime.now() + (avg_time * remaining)
                    rate = processed_count / elapsed_time.total_seconds()

                    print(
                        f"\n[Progress] {processed_count}/{len(df)} ({(processed_count/len(df))*100:.1f}%)"
                    )
                    print(
                        f"[Stats] Processed: {processed_count} | Errors: {error_count} | Rate: {rate:.1f} pairs/s"
                    )
                    print(
                        f"[Time] Elapsed: {elapsed_time} | ETA: {eta.strftime('%H:%M:%S')}"
                    )

            except Exception as e:
                error_count += 1
                print(f"[Error] {str(e)}")

    # Write any remaining results
    if results_buffer:
        write_batch_to_csv(results_buffer, first_write)

    elapsed_time = datetime.now() - start_time
    final_rate = processed_count / elapsed_time.total_seconds()

    print("\n[Complete] Summary:")
    print(
        f"Time: {elapsed_time} | Processed: {processed_count} | Errors: {error_count}"
    )
    print(f"Final rate: {final_rate:.1f} pairs/s")
    print("[Done]")


if __name__ == "__main__":
    main()
