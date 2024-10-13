import csv
import time
from datetime import timedelta

from classes.EnrichedArtifact import EnrichedArtifact

"""
Takes a reference CSV containing artifact names to process.
For each artifact, extracts relevant CVE information and details about CVE lifetimes.

Inputs:
    - (csv) CSV file containing just the artifact names

Outputs:
    - (csv) CSV file containing enriched artifact information
    - (csv) CSV file containing artifacts that have CVEs
"""

input_csv_path = "data/artifacts.csv"
output_csv_path = "data/artifacts_with_metadata.csv"
cve_output_csv_path = "data/artifacts_with_cves.csv"

with open(input_csv_path, mode="r", newline="", encoding="utf-8") as input_csv_file:
    reader = csv.reader(input_csv_file)
    rows = list(reader)

    original_headers = rows[0]
    data_rows = rows[1:]

    # Data for processing
    total_artifacts = len(data_rows)
    artifacts_with_cves = 0

    # Define new fields to be added
    metadata_fields = [
        "release_count",
        "cve_count",
        "releases_with_cves",
        "low_severity_count",
        "medium_severity_count",
        "high_severity_count",
        "critical_severity_count",
        "unknown_severity_count",
    ]

    new_headers = original_headers + metadata_fields

    start_time = time.time()

    with open(
        output_csv_path, mode="w", newline="", encoding="utf-8"
    ) as output_csv_file, open(
        cve_output_csv_path, mode="w", newline="", encoding="utf-8"
    ) as cve_output_csv_file:
        writer = csv.writer(output_csv_file)
        writer.writerow(new_headers)

        cve_writer = csv.writer(cve_output_csv_file)
        cve_writer.writerow(new_headers)

        for idx, row in enumerate(data_rows, start=1):
            artifact_name = row[0]
            enriched_artifact = EnrichedArtifact(artifact_name)

            metadata = {
                "release_count": enriched_artifact.get_total_releases(),
                "releases_with_cves": enriched_artifact.get_releases_with_cve(),
                "cve_count": enriched_artifact.get_total_cves(),
                "low_severity_count": enriched_artifact.get_severity_counts().get(
                    "LOW", 0
                ),
                "medium_severity_count": enriched_artifact.get_severity_counts().get(
                    "MODERATE", 0
                ),
                "high_severity_count": enriched_artifact.get_severity_counts().get(
                    "HIGH", 0
                ),
                "critical_severity_count": enriched_artifact.get_severity_counts().get(
                    "CRITICAL", 0
                ),
                "unknown_severity_count": enriched_artifact.get_severity_counts().get(
                    "UNKNOWN", 0
                ),
            }

            metadata_values = [metadata[field] for field in metadata_fields]
            new_row = row + metadata_values

            # Write the enriched artifact data to the main output CSV
            writer.writerow(new_row)

            # Update the count and write to CVE CSV if the artifact has CVEs
            if metadata["cve_count"] > 0:
                artifacts_with_cves += 1
                cve_writer.writerow(new_row)  # Write to the CVE-specific CSV

            # Calculate the percentage of artifacts with CVEs
            cve_percentage = (artifacts_with_cves / total_artifacts) * 100

            # Calculate elapsed time
            current_time = time.time()
            elapsed_time = current_time - start_time

            # Calculate percentage processed
            percentage_processed = (idx / total_artifacts) * 100

            # Estimate total time and ETA
            if percentage_processed > 0:
                estimated_total_time = elapsed_time / (percentage_processed / 100)
                remaining_time = estimated_total_time - elapsed_time
                eta_time = current_time + remaining_time
                eta_formatted = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(eta_time)
                )
                remaining_time_formatted = str(timedelta(seconds=int(remaining_time)))
            else:
                estimated_total_time = 0
                remaining_time = 0
                eta_formatted = "N/A"
                remaining_time_formatted = "N/A"

            # Print the cumulative count, percentage, and ETA
            print(
                f"{artifacts_with_cves}/{total_artifacts} artifacts with CVEs ({cve_percentage:.1f}%)"
            )
            print(
                f"Processed {idx}/{total_artifacts} artifacts ({percentage_processed:.1f}%), "
                f"Elapsed time: {str(timedelta(seconds=int(elapsed_time)))}, "
                f"Estimated remaining time: {remaining_time_formatted}, ETA: {eta_formatted}"
            )
