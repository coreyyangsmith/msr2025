import csv
import time
from datetime import datetime, timedelta

from ...classes.EnrichedArtifact import EnrichedArtifact
from ...classes.EnrichedRelease import EnrichedRelease
from ...classes.EnrichedCVE import EnrichedCVE
from ...utils.config import (
    RQ0_3_INPUT,
    RQ0_3_OUTPUT_RELEASES_CVES,
    FILTER_FOR_UNKNOWN_CVE_ID,
)

"""
Takes a reference CSV containing artifact names to process.
For each artifact, extracts information about each release that contains CVEs.

Inputs:
    - (csv) CSV file containing artifact names (preferably filtered for cves)

Outputs:
    - (csv) CSV file containing information about releases with CVEs
"""

input_csv_path = RQ0_3_INPUT
release_cve_output_csv_path = RQ0_3_OUTPUT_RELEASES_CVES

with open(input_csv_path, mode="r", newline="", encoding="utf-8") as input_csv_file:
    reader = csv.reader(input_csv_file)
    rows = list(reader)

    original_headers = rows[0]
    data_rows = rows[1:]

    # Data for processing
    total_artifacts = len(data_rows)
    total_cves_processed = 0
    total_cves_filtered_out = 0
    total_cves_written = 0

    # Define fields to be included in the release CSV
    release_fields = [
        "combined_name",
        "group_id",
        "artifact_id",
        "release_version",
        "release_timestamp",
        "cve_id",
        "cve_severity",
    ]

    with open(
        release_cve_output_csv_path, mode="w", newline="", encoding="utf-8"
    ) as release_cve_output_csv_file:
        writer = csv.writer(release_cve_output_csv_file)
        writer.writerow(release_fields)

        for idx, row in enumerate(data_rows, start=0):  # double check
            combined_name = row[0]
            group_id = row[1]
            artifact_id = row[2]

            enriched_artifact = EnrichedArtifact(combined_name)
            # Process each release (node) in the artifact
            for node in enriched_artifact.nodes:
                enriched_release = EnrichedRelease(node)

                release_version = enriched_release.release_version
                release_timestamp = enriched_release.release_timestamp
                release_date = enriched_release.release_date

                if len(enriched_release.cves) > 0:
                    for cve in enriched_release.cves:
                        enriched_cve = EnrichedCVE(cve)

                        cve_id = enriched_cve.id
                        total_cves_processed += 1

                        if FILTER_FOR_UNKNOWN_CVE_ID and cve_id == "UNKNOWN":
                            total_cves_filtered_out += 1
                            continue

                        cve_severity = enriched_cve.severity

                        # Build the row
                        row_data = [
                            combined_name,
                            group_id,
                            artifact_id,
                            release_version,
                            release_date,
                            cve_id,
                            cve_severity,
                        ]
                        writer.writerow(row_data)
                        total_cves_written += 1
            print(
                f"Processed {idx}/{total_artifacts} artifacts. "
                f"Total CVEs written so far: {total_cves_written}"
            )

    if total_cves_processed > 0:
        percentage_filtered = (total_cves_filtered_out / total_cves_processed) * 100
    else:
        percentage_filtered = 0

    print(f"Total CVEs processed: {total_cves_processed}")
    print(f"Total CVEs filtered out: {total_cves_filtered_out}")
    print(f"Percentage of CVEs filtered out: {percentage_filtered:.2f}%")
