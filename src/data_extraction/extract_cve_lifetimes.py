import csv
from src.classes import EnrichedArtifact

input_file_path = "data/artifacts_with_cves.csv"
output_file_path = "data/cve_lifetimes.csv"

with open(input_file_path, "r", encoding="utf-8") as infile:
    artifacts = [
        line.strip() for line in infile if line.strip()
    ]  # Remove empty lines and strip whitespace

with open(output_file_path, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    # Updated header to include Start Version and End Version
    writer.writerow(
        [
            "Artifact",
            "CVE_ID",
            "Severity",
            "Start Version",
            "End Version",
            "Start",
            "End",
            "Duration",
        ]
    )

    # Process each artifact
    for artifact in artifacts:
        # Create an EnrichedArtifact instance
        enriched_artifact = EnrichedArtifact(artifact)
        # Call the get_cve_lifetimes function
        cve_lifetimes = enriched_artifact.get_cve_lifetimes()
        # Check if cve_lifetimes is not empty or None
        if cve_lifetimes:
            # Iterate over the CVE lifetimes
            for cve, info in cve_lifetimes.items():
                # Try to get the version, start_version, and end_version from the info dictionary
                start_version = info.get("start_version", "N/A")
                end_version = info.get("end_version", "N/A")
                severity = info.get("severity", "N/A")
                # Write each CVE entry to the CSV file
                print(cve)
                writer.writerow(
                    [
                        artifact,
                        cve,
                        severity,
                        start_version,
                        end_version,
                        info["start"],
                        info["end"],
                        info["duration"],
                    ]
                )
        else:
            # Handle cases where no CVEs are returned
            writer.writerow(
                [
                    artifact,
                    "No CVEs found",
                    "N/A",
                    "N/A",
                    "N/A",
                    "N/A",
                    "N/A",
                    "N/A",
                ]
            )
