import csv
import math
import logging
import time
import concurrent.futures
from neo4j import GraphDatabase
from queue import Queue
from threading import Lock

from ...utils.config import (
    MAX_ARTIFACTS,
    ARTIFACTS_REQ_BATCH_SIZE,
    RQ0_1_OUTPUT_FILENAME,
    NEO4J_BOLT_URL,
    NEO4J_AUTH,
    MAX_WORKERS,
)

"""
1_extract_artifact_names_from_api.py

Iterates through all artifacts hosted within our dataset.
Requires a hosted Neo4J Instance containing 'with_maven_2024_08_30' dataset.
Does not require Goblin Weaver API to run

Requires:
    * Neo4j instance running with bolt connection

Output:
    * data/artifacts.csv
"""

# Initialize global variables
max_artifacts = MAX_ARTIFACTS
batch_size = ARTIFACTS_REQ_BATCH_SIZE
output_filename = RQ0_1_OUTPUT_FILENAME
csv_lock = Lock()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def process_batch(driver, skip_value, limit):
    try:
        with driver.session() as session:
            # Query for batch of artifacts
            query = """
                MATCH (a:Artifact) 
                RETURN a.id AS artifact 
                ORDER BY a.id 
                SKIP $skip 
                LIMIT $limit
            """
            result = session.run(query, skip=skip_value, limit=limit)
            artifacts = [record["artifact"] for record in result]

            # Write to CSV with lock to prevent concurrent writes
            with csv_lock:
                with open(
                    output_filename, "a", newline="", encoding="utf-8"
                ) as csvfile:
                    writer = csv.writer(csvfile)
                    for name in artifacts:
                        writer.writerow([name])

            logging.info(
                f"Processed batch: artifacts {skip_value + 1} to {skip_value + limit}"
            )
            return len(artifacts)

    except Exception as e:
        logging.error(f"Error processing batch starting at {skip_value}: {str(e)}")
        return 0


def main():
    start_time = time.time()

    # Connect to Neo4j
    driver = GraphDatabase.driver(NEO4J_BOLT_URL, auth=NEO4J_AUTH)

    try:
        # Get total artifact count
        with driver.session() as session:
            result = session.run(
                "MATCH (a:Artifact) RETURN count(a) AS total_artifacts"
            )
            total_artifacts = result.single()["total_artifacts"]
            logging.info(f"Total artifacts in database: {total_artifacts}")

        # Apply max artifacts limit
        total_artifacts = min(total_artifacts, max_artifacts)
        total_batches = math.ceil(total_artifacts / batch_size)
        logging.info(
            f"Processing {total_artifacts} artifacts in {total_batches} batches using {MAX_WORKERS} threads"
        )

        # Clear/create output file
        with open(output_filename, "w", newline="", encoding="utf-8") as csvfile:
            pass

        # Process batches using thread pool
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = []
            for batch_number in range(total_batches):
                skip_value = batch_number * batch_size
                limit = min(batch_size, total_artifacts - skip_value)

                future = executor.submit(process_batch, driver, skip_value, limit)
                futures.append(future)

            # Wait for all batches to complete
            processed_artifacts = sum(
                future.result() for future in concurrent.futures.as_completed(futures)
            )
            logging.info(f"Successfully processed {processed_artifacts} artifacts")

    finally:
        driver.close()

    elapsed_time = time.time() - start_time
    logging.info(f"Total elapsed time: {elapsed_time:.2f} seconds")


if __name__ == "__main__":
    main()
