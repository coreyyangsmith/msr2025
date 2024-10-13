import csv
import requests
import logging
import math

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

headers = {"Content-Type": "application/json", "Accept": "application/json"}
url = "http://localhost:8080/cypher"
batch_size = 1000  # Adjust the batch size as needed

# Read artifact IDs from 'artifacts.csv'
logging.info("Reading artifacts from 'artifacts.csv'...")
with open("artifacts.csv", "r", newline="", encoding="utf-8") as csvfile:
    reader = csv.reader(csvfile)
    artifact_ids = [row[0] for row in reader]

total_artifacts = len(artifact_ids)
logging.info(f"Total artifacts to be processed: {total_artifacts}")

total_batches = math.ceil(total_artifacts / batch_size)
logging.info(
    f"Processing artifacts in {total_batches} batches of up to {batch_size} artifacts each."
)

# Initialize the output CSV file
with open("latest_releases.csv", "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    # Updated headers to include 'version'
    writer.writerow(
        [
            "Artifact ID",
            "Release ID",
            "Release Timestamp",
            "Release Version",
            "No Release",
        ]
    )

# Process artifacts in batches
for batch_number in range(total_batches):
    batch_start = batch_number * batch_size
    batch_ids = artifact_ids[batch_start : batch_start + batch_size]
    logging.info(
        f"Processing batch {batch_number + 1}/{total_batches} "
        f"(Artifacts {batch_start + 1} to {batch_start + len(batch_ids)})"
    )

    # Construct the query
    artifact_ids_str = ", ".join([f'"{id}"' for id in batch_ids])
    cypher_query = f"""
    WITH [{artifact_ids_str}] AS artifactIds
    UNWIND artifactIds AS artifactId
    MATCH (a:Artifact {{id: artifactId}})
    OPTIONAL MATCH (a)-[:relationship_AR]->(r:Release)
    WITH a, r
    ORDER BY r.timestamp DESC
    WITH a, COLLECT(r)[0] AS latestRelease
    RETURN a.id AS artifactId,
           latestRelease.id AS releaseId,
           latestRelease.timestamp AS releaseTimestamp,
           latestRelease.version AS releaseVersion
    """

    query_payload = {
        "query": cypher_query,
        "parameters": {},  # Use "parameters" instead of "addedValues"
    }

    try:
        # Send the request
        response = requests.post(url, json=query_payload, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Parse the response
        data = response.json()
        columns = data.get("columns", [])
        rows = data.get("data", [])

        # Determine the index of each column
        try:
            artifact_id_idx = columns.index("artifactId")
            release_id_idx = columns.index("releaseId")
            release_timestamp_idx = columns.index("releaseTimestamp")
            release_version_idx = columns.index("releaseVersion")
        except ValueError as e:
            logging.error(f"Expected column missing in response: {e}")
            continue  # Skip this batch

        # Append the results to the output CSV file
        with open("latest_releases.csv", "a", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            for row in rows:
                artifact_id = row[artifact_id_idx]
                release_id = row[release_id_idx]
                release_timestamp = row[release_timestamp_idx]
                release_version = row[release_version_idx]

                if release_id:
                    # Extract properties from the latest release
                    writer.writerow(
                        [
                            artifact_id,
                            release_id,
                            release_timestamp,
                            release_version,
                            "",
                        ]
                    )
                else:
                    writer.writerow([artifact_id, "", "", "", "No release"])

        logging.info(f"Batch {batch_number + 1} processed successfully.")

    except requests.exceptions.RequestException as e:
        logging.error(
            f"An error occurred while processing batch {batch_number + 1}: {e}"
        )
    except KeyError as e:
        logging.error(f"Unexpected response format in batch {batch_number + 1}: {e}")
    except ValueError as e:
        logging.error(f"Error processing columns in batch {batch_number + 1}: {e}")
