import pandas as pd
import time
from datetime import datetime
from tqdm import tqdm
import concurrent.futures
from packaging import version
from src.utils.config import NEO4J_BOLT_URL, NEO4J_AUTH, MAX_WORKERS
from neo4j import GraphDatabase

"""
This script analyzes the dependency relationships between artifacts and their releases by querying a Neo4j database using the Bolt protocol.
It performs the following tasks:

1. Reads the dependency relationships from rq3_2_dependent_artifacts.csv
2. For each parent-dependent pair:
   - Queries Neo4j to get release information about the dependency relationship
   - Extracts release versions, timestamps, and dependency versions
   - Keeps only the highest version within affected versions
3. Continuously saves the enriched dependency data to a CSV file
4. Handles retries and backoff for any transient errors
"""

# Constants
MAX_RETRIES = 1
INITIAL_BACKOFF = 1
BACKOFF_FACTOR = 2
OUTPUT_FILE = "data/rq3_3_release_dependencies.csv"

# Global counters
total_relationships_scanned = 0

# Initialize the Neo4j driver
driver = GraphDatabase.driver(NEO4J_BOLT_URL, auth=NEO4J_AUTH)


def test_neo4j_connection():
    """Test the Neo4j connection with a simple query"""
    print("[Test] Testing Neo4j connection...")
    test_query = "MATCH (n) RETURN count(n) as count LIMIT 1"

    try:
        with driver.session() as session:
            result = session.run(test_query)
            count = result.single()["count"]
            print(f"[Test] Neo4j connection successful! Node count: {count}")
        return True
    except Exception as e:
        print(f"[Test] Neo4j connection failed: {str(e)}")
        return False


def query_neo4j(parent_artifact_id, dependent_artifact_id):
    """Query Neo4j for release information about a dependency relationship"""
    global total_relationships_scanned
    total_relationships_scanned += 1

    query = """
    MATCH (parentArtifact:Artifact {id: $parent_artifact_id})
    MATCH (dependentArtifact:Artifact {id: $dependent_artifact_id})
    MATCH (dependentRelease:Release)<-[:relationship_AR]-(dependentArtifact)
    MATCH (dependentRelease)-[d:dependency]->(parentArtifact)
    RETURN
      dependentArtifact.id AS dependentArtifactId,
      dependentRelease.version AS dependentReleaseVersion,
      dependentRelease.timestamp AS dependentReleaseTimestamp,
      d.targetVersion AS parentReleaseVersion,
      parentArtifact.id AS parentArtifactId
    """

    parameters = {
        "parent_artifact_id": parent_artifact_id,
        "dependent_artifact_id": dependent_artifact_id
    }

    backoff = INITIAL_BACKOFF
    for attempt in range(MAX_RETRIES):
        try:
            with driver.session() as session:
                result = session.run(query, parameters)
                data = [record.data() for record in result]
                return data

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
    cve_id = row["cve_id"]

    result = query_neo4j(parent_id, dependent_id)
    if not result:
        return None
    # print(f"[Processing] Parent: {parent_id}, Dependent: {dependent_id}")

    releases_affected = {}
    releases_patched = {}
    versions_processed = 0
    versions_skipped = 0

    for record in result:
        dep_id = record["dependentArtifactId"]
        dep_version = record["dependentReleaseVersion"]
        timestamp = record["dependentReleaseTimestamp"]
        parent_version = record["parentReleaseVersion"]
        parent_artifact_id = record["parentArtifactId"]

        # Case 1: Highest dependent_version for highest parent_version in affected_versions
        if parent_version in affected_versions:
            try:
                parsed_parent_version = version.parse(parent_version)
                parsed_dep_version = version.parse(dep_version)
                versions_processed += 1
            except version.InvalidVersion:
                versions_skipped += 1
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
            versions_processed += 1
        except version.InvalidVersion:
            versions_skipped += 1
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

    # Process each unique dependent ID
    unique_dep_ids = set(releases_affected.keys()) | set(releases_patched.keys())

    if not unique_dep_ids:
        # If no affected or patched versions found, create a row with none_found
        releases.append({
            "dependent_artifact_id": dependent_id,
            "affected_parent_artifact_id": None,
            "affected_parent_version": None,
            "affected_dependent_version": None,
            "affected_timestamp": None,
            "affected_date": None,
            "patched_parent_artifact_id": None,
            "patched_parent_version": None,
            "patched_dependent_version": None,
            "patched_timestamp": None,
            "patched_date": None,
            "cve_id": cve_id,
            "none_found": parent_id
        })
    else:
        for dep_id in unique_dep_ids:
            affected = releases_affected.get(dep_id)
            patched = releases_patched.get(dep_id)

            release_data = {
                "dependent_artifact_id": dep_id,
                "affected_parent_artifact_id": affected["parent_id"] if affected else None,
                "affected_parent_version": str(affected["parent_version"])
                if affected
                else None,
                "affected_dependent_version": affected["version"] if affected else None,
                "affected_timestamp": affected["timestamp"] if affected else None,
                "affected_date": datetime.fromtimestamp(
                    affected["timestamp"] / 1000
                ).strftime("%Y-%m-%d")
                if affected
                else None,
                "patched_parent_artifact_id": patched["parent_id"] if patched else None,
                "patched_parent_version": str(patched["parent_version"])
                if patched
                else None,
                "patched_dependent_version": patched["version"] if patched else None,
                "patched_timestamp": patched["timestamp"] if patched else None,
                "patched_date": datetime.fromtimestamp(
                    patched["timestamp"] / 1000
                ).strftime("%Y-%m-%d")
                if patched
                else None,
                "cve_id": cve_id,
                "none_found": None
            }

            releases.append(release_data)

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
    global driver
    print("[Start] Release Dependency Analysis")

    # Test Neo4j connection first
    if not test_neo4j_connection():
        print("[Error] Failed to connect to Neo4j. Exiting...")
        return

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

                # Log progress every 3 items
                if processed_count % 3 == 0:
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
                    print(
                        f"[Relationships] Total scanned: {total_relationships_scanned}"
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
    print(f"Total dependency relationships scanned: {total_relationships_scanned}")
    print("[Done]")

    # Close the driver
    driver.close()


if __name__ == "__main__":
    main()
