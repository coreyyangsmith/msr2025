import csv
import time
from datetime import datetime, timedelta

from classes.EnrichedArtifact import EnrichedArtifact

"""
Takes a reference CSV containing artifact names to process.
For each artifact, extracts information about each release that contains CVEs.

Inputs:
    - (csv) CSV file containing artifact names

Outputs:
    - (csv) CSV file containing information about releases with CVEs
"""

input_csv_path = "data/artifacts_with_cves.csv"
release_cve_output_csv_path = "data/releases_with_cves.csv"

with open(input_csv_path, mode="r", newline="", encoding="utf-8") as input_csv_file:
    reader = csv.reader(input_csv_file)
    rows = list(reader)

    original_headers = rows[0]
    data_rows = rows[1:]

    # Data for processing
    total_artifacts = len(data_rows)
    total_releases_with_cves = 0

    # Define fields to be included in the release CSV
    release_fields = [
        "artifact_name",
        "release_version",
        "timestamp",
        "cve_id",
        "cve_severity",
    ]

    with open(
        release_cve_output_csv_path, mode="w", newline="", encoding="utf-8"
    ) as release_cve_output_csv_file:
        writer = csv.writer(release_cve_output_csv_file)
        writer.writerow(release_fields)

        for idx, row in enumerate(data_rows, start=1):
            artifact_name = row[0]
            enriched_artifact = EnrichedArtifact(artifact_name)

            # Process each release (node) in the artifact
            for node in enriched_artifact.nodes:
                release_version = node.get("version", "UNKNOWN")
                timestamp = node.get("timestamp", None)
                if timestamp is not None:
                    # Convert timestamp to datetime object
                    release_date = datetime.fromtimestamp(timestamp / 1000).strftime(
                        "%Y-%m-%d"
                    )
                else:
                    release_date = "UNKNOWN"

                cves = node.get("cve", [])
                if len(cves) > 0:
                    for cve in cves:
                        cve_id = cve.get("name", "UNKNOWN")
                        cve_severity = cve.get("severity", "UNKNOWN").upper()

                        # Build the row
                        row_data = [
                            artifact_name,
                            release_version,
                            release_date,
                            cve_id,
                            cve_severity,
                        ]
                        writer.writerow(row_data)
                        total_releases_with_cves += 1

            # Optional: Print progress
            print(
                f"Processed {idx}/{total_artifacts} artifacts. "
                f"Total releases with CVEs so far: {total_releases_with_cves}"
            )
