import csv
import requests
import math
import logging
import time

from ...utils.config import (
    MAX_ARTIFACTS,
    ARTIFACTS_REQ_BATCH_SIZE,
    RQ0_1_OUTPUT_FILENAME,
    N4O4J_URL,
    REQ_HEADERS,
)

"""
1_extract_artifact_names_from_api.py

Iterates through all artifacts hosted within our dataset.
Requires a hosted Neo4J Instance containing 'with_maven_2024_08_30' dataset.
Does not require Goblin Weaver API to run

Requires:

Output:
    * data/artifacts.csv

"""

headers = REQ_HEADERS
url = N4O4J_URL
max_artifacts = MAX_ARTIFACTS
batch_size = ARTIFACTS_REQ_BATCH_SIZE
output_filename = RQ0_1_OUTPUT_FILENAME

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Start time measurement
start_time = time.time()

# ------------------------------------------ #
# Step 1: Retrieve Total Number of Artifacts #
# ------------------------------------------ #
logging.info("Retrieving total number of artifacts...")
count_query = {
    "query": "MATCH (a:Artifact) RETURN count(a) AS total_artifacts",
    "addedValues": [],
}

response = requests.post(url, json=count_query, headers=headers)

if response.status_code == 200:
    total_artifacts = int(response.json()["values"][0]["total_artifacts"])
    logging.info(f"Total artifacts in database: {total_artifacts}")
else:
    logging.error(
        f"Failed to retrieve total artifacts. Status code: {response.status_code}"
    )
    logging.error("Response text: %s", response.text)
    exit()

# -------------------------------- #
# Step 2: Retrieve Artifacts Names #
# -------------------------------- #
total_artifacts = min(total_artifacts, max_artifacts)
logging.info(
    f"Total artifacts to be processed (after applying max limit): {total_artifacts}"
)
total_batches = math.ceil(total_artifacts / batch_size)
logging.info(
    f"Processing artifacts in {total_batches} batches of {batch_size} artifacts each."
)

# Iteratively process batches and write names to CSV
for batch_number in range(total_batches):
    skip_value = batch_number * batch_size
    limit = min(batch_size, total_artifacts - skip_value)
    logging.info(
        f"Processing batch {batch_number + 1}/{total_batches} (Artifacts {skip_value + 1} to {skip_value + limit})"
    )

    # Step 2: Retrieve a batch of artifacts
    artifact_query = {
        "query": f"MATCH (a:Artifact) RETURN a.id AS artifact ORDER BY a.id SKIP {skip_value} LIMIT {limit}",
        "addedValues": [],
    }

    try:
        # Send the request
        response = requests.post(url, json=artifact_query, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Parse the response
        data = response.json()
        artifacts = [item["artifact"] for item in data["values"]]

        # Append the names to a CSV file
        with open(output_filename, "a", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            for name in artifacts:
                writer.writerow([name])

        print(f"Artifact names have been successfully appended to '{output_filename}'.")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
    except KeyError as e:
        print(f"Unexpected response format: {e}")

# End time measurement
end_time = time.time()
elapsed_time = end_time - start_time

# Log the total elapsed time
logging.info(f"Total elapsed time: {elapsed_time:.2f} seconds.")
