import csv
import time
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from ...classes.EnrichedArtifact import EnrichedArtifact
from ...utils.config import (
    RQ0_2_INPUT,
    RQ0_2_OUTPUT_ARTIFACTS_CVES,
    FILTER_FOR_CVES,
    FILTER_FOR_UNKNOWN_SEVERITY,
    MAX_WORKERS,
)


def process_artifact(artifact_name):
    enriched_artifact = EnrichedArtifact(artifact_name)

    metadata = {
        "combined_name": f"{enriched_artifact.group_id}:{enriched_artifact.artifact_id}",
        "group_id": enriched_artifact.group_id,
        "artifact_id": enriched_artifact.artifact_id,
        "latest_release": enriched_artifact.latest_release,
        "release_count": enriched_artifact.get_total_releases(),
        "releases_with_cves": enriched_artifact.get_releases_with_cve(),
        "total_releases_cve_count": enriched_artifact.get_total_cves(),
        "low_severity_count": enriched_artifact.get_severity_counts().get("LOW", 0),
        "moderate_severity_count": enriched_artifact.get_severity_counts().get(
            "MODERATE", 0
        ),
        "high_severity_count": enriched_artifact.get_severity_counts().get("HIGH", 0),
        "critical_severity_count": enriched_artifact.get_severity_counts().get(
            "CRITICAL", 0
        ),
        "unknown_severity_count": enriched_artifact.get_severity_counts().get(
            "UNKNOWN", 0
        ),
    }

    include_artifact = True

    if FILTER_FOR_CVES and metadata["total_releases_cve_count"] == 0:
        include_artifact = False

    if FILTER_FOR_UNKNOWN_SEVERITY and metadata["unknown_severity_count"] > 0:
        include_artifact = False

    if include_artifact:
        metadata_values = [metadata[field] for field in metadata_fields]
        return metadata_values
    return None


"""
    Takes a reference CSV containing artifact names to process.
    For each artifact, extracts relevant CVE information and details about CVE lifetimes.

    Inputs:
        - (csv) CSV file containing just the artifact names

    Outputs:
        - (csv) CSV file containing enriched artifacts with cve counts (incl. headers)
"""

input_csv_path = RQ0_2_INPUT
output_csv_path = RQ0_2_OUTPUT_ARTIFACTS_CVES

print("\n\n 2_enrich_artifact_data \n\n")

with open(input_csv_path, mode="r", newline="", encoding="utf-8") as input_csv_file:
    reader = csv.reader(input_csv_file)
    rows = list(reader)

    data_rows = rows[0:]  # no headers

    # Data for processing
    total_artifacts = len(data_rows)
    written_artifacts = 0

    # Define new fields to be added
    metadata_fields = [
        "combined_name",
        "group_id",
        "artifact_id",
        "latest_release",
        "release_count",
        "releases_with_cves",
        "total_releases_cve_count",
        "low_severity_count",
        "moderate_severity_count",
        "high_severity_count",
        "critical_severity_count",
        "unknown_severity_count",
    ]

    new_headers = metadata_fields

    start_time = time.time()

    with open(
        output_csv_path, mode="w", newline="", encoding="utf-8"
    ) as output_csv_file:
        writer = csv.writer(output_csv_file)
        writer.writerow(new_headers)

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_idx = {
                executor.submit(process_artifact, row[0]): idx
                for idx, row in enumerate(data_rows, start=1)
            }

            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    result = future.result()
                    if result:
                        written_artifacts += 1
                        writer.writerow(result)
                except Exception as e:
                    print(f"Error processing artifact at index {idx}: {e}")

                # Calculate the percentage of artifacts processed
                percentage_processed = (idx / total_artifacts) * 100

                # Calculate the percentage of artifacts with CVEs
                if idx > 0:
                    cve_percentage = (written_artifacts / idx) * 100
                else:
                    cve_percentage = 0.0

                # Calculate elapsed time
                current_time = time.time()
                elapsed_time = current_time - start_time

                # Estimate total time and ETA
                if percentage_processed > 0:
                    estimated_total_time = elapsed_time / (percentage_processed / 100)
                    remaining_time = estimated_total_time - elapsed_time
                    eta_time = current_time + remaining_time
                    eta_formatted = time.strftime(
                        "%Y-%m-%d %H:%M:%S", time.localtime(eta_time)
                    )
                    remaining_time_formatted = str(
                        timedelta(seconds=int(remaining_time))
                    )
                else:
                    estimated_total_time = 0
                    remaining_time = 0
                    eta_formatted = "N/A"
                    remaining_time_formatted = "N/A"

                # Print the cumulative count, percentage, and ETA
                print(
                    f"{written_artifacts}/{idx} artifacts with CVEs ({cve_percentage:.1f}%)"
                )
                print(
                    f"Processed {idx}/{total_artifacts} artifacts ({percentage_processed:.1f}%), "
                    f"Elapsed time: {str(timedelta(seconds=int(elapsed_time)))}, "
                    f"Estimated remaining time: {remaining_time_formatted}, ETA: {eta_formatted}"
                )
