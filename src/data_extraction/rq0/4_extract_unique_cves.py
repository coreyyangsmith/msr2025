import csv
import time
from src.classes import EnrichedArtifact
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from ...utils.config import (
    RQ0_4_INPUT,
    RQ0_4_OUTPUT_UNIQUE_CVES,
    FILTER_FOR_INVALID_DATA,
    MAX_WORKERS,
)


def format_time(seconds):
    mins, secs = divmod(int(seconds), 60)
    hours, mins = divmod(mins, 60)
    return f"{hours:02d}:{mins:02d}:{secs:02d}"


def process_artifact(combined_name):
    rows = []
    local_filtered_cve = 0
    local_total_cve = 0

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
            start_version_timestamp = info.get("start_version_timestamp", "N/A")
            start_version_date = info.get("start_version_date", "N/A")

            end_version = info.get("end_version", "N/A")
            end_version_timestamp = info.get("end_version_timestamp", "N/A")
            end_version_date = info.get("end_version_date", "N/A")

            patched_version = info.get("patched_version", "N/A")
            patched_version_timestamp = info.get("patched_version_timestamp", "N/A")
            patched_version_date = info.get("patched_version_date", "N/A")

            latest_version = enriched_artifact.latest_release

            cve_patched = enriched_artifact.is_latest_release(end_version)
            cve_publish_date = info.get("cve_publish_date", "N/A")
            cve_duration = info.get("duration", "N/A")

            api_id = info.get("api_id", "N/A")
            api_aliases = info.get("api_aliases", "N/A")

            if cve_duration != "N/A":
                try:
                    duration_value = float(cve_duration)
                    if cve_patched and duration_value < 0:
                        data_class = 0  # fast patch
                    elif cve_patched and duration_value >= 0:
                        data_class = 1  # slow patch
                    else:
                        data_class = 2  # no patch
                except ValueError:
                    data_class = -1  # invalid data
            else:
                data_class = -1  # invalid data

            # Check for invalid data if the flag is True
            local_total_cve += 1
            if FILTER_FOR_INVALID_DATA:
                if cve_publish_date == "" and cve_duration == "N/A":
                    local_filtered_cve += 1
                    continue  # Skip to the next cve_lifetime

            row = [
                data_class,
                combined_name,
                group_id,
                artifact_id,
                cve_id,
                severity,
                cve_patched,
                cve_publish_date,
                cve_duration,
                start_version,
                start_version_timestamp,
                start_version_date,
                end_version,
                end_version_timestamp,
                end_version_date,
                patched_version,
                patched_version_timestamp,
                patched_version_date,
                latest_version,
                api_id,
                api_aliases,
            ]
            rows.append(row)
    else:
        row = [
            -1,  # Assuming data_class for no CVE found
            combined_name,
            group_id,
            artifact_id,
            "No CVE Found",
            "N/A",
            "N/A",
            "N/A",
            "N/A",
            "N/A",
            "N/A",
            "N/A",
            "N/A",
            "N/A",
            "N/A",
            "N/A",
            "N/A",
            "N/A",
            "N/A",
            "N/A",
            "N/A",
        ]
        rows.append(row)

    return rows, local_filtered_cve, local_total_cve


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

total_artifacts = len(artifacts)
print(f"Total number of artifacts to process: {total_artifacts}")

start_time = time.time()
processed_artifacts = 0

lock = Lock()

with open(output_file_path, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(
        [
            "data_class",
            "combined_name",
            "group_id",
            "artifact_id",
            "cve_id",
            "severity",
            "cve_patched",
            "cve_publish_date",
            "cve_duration",
            "start_version",
            "start_version_timestamp",
            "start_version_date",
            "end_version",
            "end_version_timestamp",
            "end_version_date",
            "patched_version",
            "patched_version_timestamp",
            "patched_version_date",
            "latest_version",
            "api_id",
            "api_aliases",
        ]
    )

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_artifact = {
            executor.submit(process_artifact, artifact): artifact
            for artifact in artifacts
        }

        for future in as_completed(future_to_artifact):
            artifact = future_to_artifact[future]
            try:
                rows, local_filtered, local_total = future.result()
            except Exception as e:
                print(f"Error processing artifact '{artifact}': {e}")
                continue

            with lock:
                writer.writerows(rows)
                filtered_cve_count += local_filtered
                total_cve_count += local_total
                processed_artifacts += 1

                percentage_complete = (processed_artifacts / total_artifacts) * 100
                elapsed_time = time.time() - start_time
                if processed_artifacts > 0:
                    average_time_per_artifact = elapsed_time / processed_artifacts
                    time_remaining = average_time_per_artifact * (
                        total_artifacts - processed_artifacts
                    )
                    time_remaining_formatted = format_time(time_remaining)
                else:
                    time_remaining_formatted = "N/A"

                print(
                    f"Progress: {processed_artifacts}/{total_artifacts} artifacts processed "
                    f"({percentage_complete:.2f}% complete). Estimated time remaining: {time_remaining_formatted}"
                )

# After processing all artifacts, print the total number of filtered cve_lifetimes
print(
    f"Number of filtered CVE lifetimes due to invalid data: {filtered_cve_count}/{total_cve_count}"
)
