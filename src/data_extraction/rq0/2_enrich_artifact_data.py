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

    severity_counts = enriched_artifact.get_severity_counts()

    metadata = {
        "combined_name": f"{enriched_artifact.group_id}:{enriched_artifact.artifact_id}",
        "group_id": enriched_artifact.group_id,
        "artifact_id": enriched_artifact.artifact_id,
        "latest_release": enriched_artifact.latest_release,
        "release_count": enriched_artifact.get_total_releases(),
        "releases_with_cves": enriched_artifact.get_releases_with_cve(),
        "total_releases_cve_count": enriched_artifact.get_total_cves(),
        "low_severity_count": severity_counts.get("LOW", 0),
        "moderate_severity_count": severity_counts.get("MODERATE", 0),
        "high_severity_count": severity_counts.get("HIGH", 0),
        "critical_severity_count": severity_counts.get("CRITICAL", 0),
        "unknown_severity_count": severity_counts.get("UNKNOWN", 0),
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

print("\n\nStarting 2_enrich_artifact_data...\n")
print(f"Input CSV Path: {input_csv_path}")
print(f"Output CSV Path: {output_csv_path}\n")

with open(input_csv_path, mode="r", newline="", encoding="utf-8") as input_csv_file:
    reader = csv.reader(input_csv_file)
    rows = list(reader)

    data_rows = rows[0:]  # no headers

    # Data for processing
    total_artifacts = len(data_rows)
    written_artifacts = 0

    print(f"Total artifacts to process: {total_artifacts}\n")

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
        print(f"CSV headers written: {new_headers}\n")

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            print(f"ThreadPoolExecutor initialized with {MAX_WORKERS} workers.\n")
            future_to_idx = {
                executor.submit(process_artifact, row[0]): idx
                for idx, row in enumerate(data_rows, start=1)
            }
            print("Submitted all artifacts to the executor.\n")

            total_futures_completed = 0

            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                total_futures_completed += 1

                try:
                    result = future.result()
                    if result:
                        written_artifacts += 1
                        writer.writerow(result)
                        if written_artifacts % 1000 == 0:
                            print(
                                f"{written_artifacts} artifacts with CVEs written so far."
                            )
                except Exception as e:
                    print(f"Error processing artifact at index {idx}: {e}")

                # Calculate the percentage of artifacts processed
                percentage_processed = (total_futures_completed / total_artifacts) * 100

                # Calculate the percentage of artifacts with CVEs
                if total_futures_completed > 0:
                    cve_percentage = (written_artifacts / total_futures_completed) * 100
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
                    f"{written_artifacts}/{total_futures_completed} artifacts with CVEs ({cve_percentage:.1f}%)"
                )
                print(
                    f"Processed {total_futures_completed}/{total_artifacts} artifacts ({percentage_processed:.2f}%), "
                    f"Elapsed time: {str(timedelta(seconds=int(elapsed_time)))}, "
                    f"Estimated remaining time: {remaining_time_formatted}, ETA: {eta_formatted}\n"
                )

    total_elapsed_time = time.time() - start_time
    print(f"\nCompleted processing {total_artifacts} artifacts.")
    print(
        f"Artifacts with CVEs: {written_artifacts} ({(written_artifacts/total_artifacts)*100:.2f}%)"
    )
    print(f"Total elapsed time: {str(timedelta(seconds=int(total_elapsed_time)))}\n")
