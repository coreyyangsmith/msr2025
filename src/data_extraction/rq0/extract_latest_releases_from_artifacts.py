import csv
import requests
import logging
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Neo4j HTTP API configuration
headers = {"Content-Type": "application/json", "Accept": "application/json"}
url = "http://localhost:8080/cypher"

# Setup a session with retry strategy to handle transient network issues
session = requests.Session()
retry = Retry(
    total=5,  # Total number of retries
    backoff_factor=1,  # Exponential backoff factor
    status_forcelist=[502, 503, 504],  # HTTP status codes to retry
    allowed_methods=["POST"],  # Methods to retry
)
adapter = HTTPAdapter(max_retries=retry)
session.mount("http://", adapter)
session.mount("https://", adapter)

# Read artifact IDs from 'artifacts.csv'
logging.info("Reading artifacts from 'artifacts.csv'...")
try:
    with open("artifacts.csv", "r", newline="", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        artifact_ids = [row[0].strip() for row in reader if row]
except FileNotFoundError:
    logging.error("The file 'artifacts.csv' was not found.")
    exit(1)
except Exception as e:
    logging.error(f"An error occurred while reading 'artifacts.csv': {e}")
    exit(1)

total_artifacts = len(artifact_ids)
logging.info(f"Total artifacts to be processed: {total_artifacts}")

# Initialize the output CSV file with headers
csv_headers = [
    "Artifact ID",
    "Release ID",
    "Release Timestamp",
    "Release Version",
    "No Release",
]

try:
    with open("latest_releases.csv", "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(csv_headers)
except Exception as e:
    logging.error(f"An error occurred while initializing 'latest_releases.csv': {e}")
    exit(1)


# Function to parse a list of single-key dictionaries
def parse_response(response_list):
    artifact_data = {
        "artifactId": "",
        "releaseId": "",
        "releaseTimestamp": "",
        "releaseVersion": "",
    }
    for item in response_list:
        if not isinstance(item, dict) or len(item) != 1:
            continue  # Skip invalid entries
        key, value = next(iter(item.items()))
        if key in artifact_data:
            artifact_data[key] = value
    return artifact_data


# Process each artifact individually
with open("latest_releases.csv", "a", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)

    for index, artifact_id in enumerate(artifact_ids, start=1):
        logging.info(f"Processing artifact {index}/{total_artifacts}: {artifact_id}")

        # Construct the Cypher query using parameters to prevent injection
        cypher_query = f"""
        MATCH (a:Artifact {artifact_id})
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
            "addedValues": [],
        }

        try:
            # Send the POST request to Neo4j
            response = session.post(url, json=query_payload, headers=headers)
            response.raise_for_status()  # Raise an exception for HTTP errors

            # Parse the JSON response
            data = response.json()

            # Check if 'values' key exists and is a list
            if "values" not in data or not isinstance(data["values"], list):
                logging.error(
                    f"Invalid response format for artifact {artifact_id}: {data}"
                )
                writer.writerow([artifact_id, "", "", "", "Invalid response format"])
                continue  # Skip to the next artifact

            results = data.get("values", [])

            # Parse the response list of single-key dictionaries
            artifact_data = parse_response(results)

            # Extract fields
            a_id = artifact_data.get("artifactId", "").strip()
            r_id = artifact_data.get("releaseId", "").strip()
            r_timestamp = artifact_data.get("releaseTimestamp", "").strip()
            r_version = artifact_data.get("releaseVersion", "").strip()

            # Handle 'NULL' values and missing releases
            if r_id and r_id.upper() != "NULL":
                writer.writerow(
                    [
                        a_id,
                        r_id,
                        r_timestamp,
                        r_version,
                        "",
                    ]
                )
            else:
                writer.writerow([a_id, "", "", "", "No release"])

            logging.info(f"Artifact {index}/{total_artifacts} processed successfully.")

        except requests.exceptions.RequestException as e:
            logging.error(f"HTTP error for artifact {artifact_id}: {e}")
            writer.writerow([artifact_id, "", "", "", "HTTP error"])
        except ValueError as e:
            logging.error(f"JSON decoding failed for artifact {artifact_id}: {e}")
            writer.writerow([artifact_id, "", "", "", "JSON decode error"])
        except Exception as e:
            logging.error(f"Unexpected error for artifact {artifact_id}: {e}")
            writer.writerow([artifact_id, "", "", "", "Unexpected error"])

logging.info("All artifacts have been processed.")
