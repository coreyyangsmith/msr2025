import csv
from src.classes import EnrichedArtifact

from ...utils.config import (
    RQ0_4_INPUT,
    RQ0_4_OUTPUT_UNIQUE_CVES,
    FILTER_FOR_INVALID_DATA,
)

input_file_path = RQ0_4_INPUT
output_file_path = RQ0_4_OUTPUT_UNIQUE_CVES

filtered_cve_count = 0
total_cve_count = 0
artifacts = []

with open(input_file_path, mode="r", encoding="utf-8", newline="") as infile:
    reader = csv.DictReader(infile)
    if "combined_name" not in reader.fieldnames:
        raise ValueError("The 'combined_name' column is missing from the CSV file.")

    for row in reader:
        combined_name = row.get("combined_name", "").strip()
        if combined_name:  # Ensure it's not empty after stripping
            artifacts.append(combined_name)

with open(output_file_path, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    # Updated header to include Start Version and End Version
    writer.writerow(
        [
            "combined_name",
            "group_id",
            "artifact_id",
            "cve_id",
            "severity",
            "start_version",
            "end_version",
            "patched_version",
            "latest_version",
            "start_version_timestamp",
            "end_version_timestamp",
            "patched_version_timestamp",
            "cve_publish_date",
            "cve_patched",
            "cve_duration",
            "api_id",
            "api_aliases",
        ]
    )

    for combined_name in artifacts:
        enriched_artifact = EnrichedArtifact(combined_name)
        group_id = enriched_artifact.group_id
        artifact_id = enriched_artifact.artifact_id

        cve_lifetimes = enriched_artifact.get_cve_lifetimes()

        if cve_lifetimes:
            # Iterate over the CVE lifetimes
            for cve, info in cve_lifetimes.items():
                cve_id = cve
                severity = info.get("severity", "N/A")
                start_version = info.get("start_version", "N/A")
                end_version = info.get("end_version", "N/A")
                patched_version = info.get("patched_version", "N/A")
                latest_version = enriched_artifact.latest_release
                start_version_timestamp = info.get("start_version_timestamp", "N/A")
                end_version_timestamp = info.get("end_version_timestamp", "N/A")
                patched_version_timestamp = info.get("patched_version_timestamp", "N/A")
                cve_publish_date = info.get("cve_publish_date", "N/A")
                cve_patched = enriched_artifact.is_latest_release(end_version)
                cve_duration = info.get("duration", "N/A")
                api_id = info.get("api_id", "N/A")
                api_aliases = info.get("api_aliases", "N/A")

                # Check for invalid data if the flag is True
                total_cve_count += 1
                if FILTER_FOR_INVALID_DATA:
                    if cve_publish_date == "" and cve_duration == "N/A":
                        filtered_cve_count += 1
                        continue  # Skip to the next cve_lifetime

                print(cve)

                writer.writerow(
                    [
                        combined_name,
                        group_id,
                        artifact_id,
                        cve_id,
                        severity,
                        start_version,
                        end_version,
                        patched_version,
                        latest_version,
                        start_version_timestamp,
                        end_version_timestamp,
                        patched_version_timestamp,
                        cve_publish_date,
                        cve_patched,
                        cve_duration,
                        api_id,
                        api_aliases,
                    ]
                )
        else:
            writer.writerow(
                [
                    combined_name,
                    group_id,
                    artifact_id,
                    "No CVEs found",
                    "N/A",
                    "N/A",
                    "N/A",
                    "N/A",
                    latest_version,
                    "N/A",
                    "N/A",
                    "N/A",
                    "N/A",
                    "N/A",
                    "N/A",
                    "N/A",
                ]
            )

# After processing all artifacts, print the total number of filtered cve_lifetimes
print(
    f"Number of filtered CVE lifetimes due to invalid data: {filtered_cve_count}/{total_cve_count}"
)
