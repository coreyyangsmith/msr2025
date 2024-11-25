import pandas as pd
import requests
import logging
import os
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from src.utils.config import MAX_WORKERS, NEO4J_URL

"""
This script reads a CSV file containing parent-dependency pairs and retrieves the dependent versions
that have a matching parent version from our local Neo4j database.

Tasks:
1. Reads the `rq3_3_unique_dependencies.csv` file containing parent-dependency pairs.
2. For each pair:
   - Queries Neo4j to find all dependent releases that depend on the parent artifact
   - For each dependent release, checks if it has a matching parent version
3. Saves the retrieved dependent version, parent version and timestamp information to a new CSV file.
4. Logs processing statistics and errors.
"""

# Constants for controlling concurrency
DEPENDENT_VERSIONS_WORKERS = MAX_WORKERS // 2

thread_local = threading.local()
output_lock = threading.Lock()


def process_dependency_pair(row):
    """Process a single dependency pair by checking all versions for matching parent."""
    dependent = row["dependent"]
    parent = row["parent"]
    results = []

    logging.info(
        f"Processing dependency pair - Parent: {parent}, Dependent: {dependent}"
    )

    try:
        parent_group_id, parent_artifact_id = parent.split(":")
        dependent_group_id, dependent_artifact_id = dependent.split(":")
    except ValueError:
        logging.error(f"Invalid format - parent: {parent}, dependent: {dependent}")
        return results

    try:
        # Construct Cypher query to find matching dependencies
        query = f"""
        MATCH (parentArtifact:Artifact {{groupId: "{parent_group_id}", artifactId: "{parent_artifact_id}"}})
        MATCH (dependentRelease:Release)-[:dependency]->(parentArtifact)
        MATCH (dependentArtifact:Artifact)<-[:relationship_AR]-(dependentRelease)
        WHERE dependentArtifact.groupId = "{dependent_group_id}" 
        AND dependentArtifact.artifactId = "{dependent_artifact_id}"
        RETURN dependentRelease.version as dependent_version,
               dependentRelease.timestamp as timestamp,
               dependentRelease.parentVersion as parent_version
        """

        # Send request to Neo4j
        headers = {"Content-Type": "application/json"}
        payload = {"statements": [{"statement": query}]}
        response = requests.post(
            f"{NEO4J_URL}/db/data/transaction/commit", headers=headers, json=payload
        )
        response.raise_for_status()
        data = response.json()

        for row in data["results"][0]["data"]:
            dependent_version = row["row"][0]
            timestamp = row["row"][1]
            parent_version = row["row"][2]

            if parent_version:  # Only include if parent version exists
                logging.info(
                    f"Found matching version: {dependent}:{dependent_version} -> {parent}:{parent_version}"
                )
                results.append(
                    {
                        "parent": parent,
                        "parent_version": parent_version,
                        "dependent": dependent,
                        "dependent_version": dependent_version,
                        "timestamp": timestamp,
                    }
                )

    except requests.RequestException as e:
        logging.error(f"Error processing {dependent}: {e}")

    logging.info(f"Found {len(results)} matches for {dependent}")
    return results


def extract_dependent_versions(input_path, output_path):
    """Extract dependent versions with matching parent versions from Neo4j."""
    dependency_pairs_df = pd.read_csv(input_path)
    total_pairs = len(dependency_pairs_df)
    logging.info(f"Starting to fetch and analyze {total_pairs} dependent versions...")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Initialize output file with headers
    logging.info(f"Creating output file: {output_path}")
    with open(output_path, "w") as f:
        f.write("parent,parent_version,dependent,dependent_version,timestamp\n")

    completed = 0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=DEPENDENT_VERSIONS_WORKERS) as executor:
        futures = [
            executor.submit(process_dependency_pair, row)
            for _, row in dependency_pairs_df.iterrows()
        ]

        for future in as_completed(futures):
            completed += 1
            results = future.result()
            with output_lock:
                with open(output_path, "a") as f:
                    for result in results:
                        line = f"{result['parent']},{result['parent_version']},{result['dependent']},{result['dependent_version']},{result['timestamp']}\n"
                        f.write(line)

            # Calculate progress statistics
            elapsed_time = time.time() - start_time
            pairs_per_second = completed / elapsed_time if elapsed_time > 0 else 0
            remaining_pairs = total_pairs - completed
            eta_seconds = (
                remaining_pairs / pairs_per_second if pairs_per_second > 0 else 0
            )

            progress = (completed / total_pairs) * 100
            logging.info(f"Progress: {progress:.2f}% ({completed}/{total_pairs})")
            logging.info(f"Processing rate: {pairs_per_second:.2f} pairs/second")
            logging.info(f"Estimated time remaining: {int(eta_seconds)} seconds")

    logging.info(f"Completed analysis. Results saved to {output_path}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("rq3_dependent_versions.log"),
            logging.StreamHandler(),
        ],
    )

    input_path = "data/rq3_3_unique_dependencies.csv"
    output_path = "data/rq3_4_dependent_versions.csv"

    extract_dependent_versions(input_path, output_path)
