import pandas as pd
import re
from datetime import datetime
from packaging import version

# Read the input files
rq3_3_df = pd.read_csv("data/rq3_3_relevant_releases.csv")
rq0_4_df = pd.read_csv("data/rq0_4_unique_cves.csv")

# Convert date strings to datetime objects, ensuring timezone-naive comparison
rq3_3_df["target_dependent_release_date"] = pd.to_datetime(
    rq3_3_df["target_dependent_release_date"]
).dt.tz_localize(None)
rq0_4_df["patched_version_date"] = pd.to_datetime(
    rq0_4_df["patched_version_date"]
).dt.tz_localize(None)
rq0_4_df["cve_publish_date"] = pd.to_datetime(
    rq0_4_df["cve_publish_date"]
).dt.tz_localize(None)

# Initialize list to store matching rows
matching_rows = []

# Keep track of processed CVEs for each target_dependency + parent combo
processed_cves = set()

# Track minimum version per unique key that's >= patched version
min_versions = {}

# Add debug prints
print("Number of rows in rq3_3_df:", len(rq3_3_df))
print("Number of rows in rq0_4_df:", len(rq0_4_df))
print("\nSample of rq3_3_df:")
print(rq3_3_df[["parent_artifact-group", "parent_version"]].head())
print("\nSample of rq0_4_df:")
print(rq0_4_df[["combined_name", "patched_version"]].head())

# For each row in rq3_3
for _, rq3_row in rq3_3_df.iterrows():
    # Find matching CVEs for this parent artifact
    matching_cves = rq0_4_df[
        rq0_4_df["combined_name"] == rq3_row["parent_artifact-group"]
    ]

    print(f"\nProcessing parent: {rq3_row['parent_artifact-group']}")
    print(f"Found {len(matching_cves)} matching CVEs")

    # For each matching CVE
    for _, cve_row in matching_cves.iterrows():
        print(f"\nProcessing CVE: {cve_row['cve_id']}")
        print(f"Release date: {rq3_row['target_dependent_release_date']}")
        print(f"CVE patch date: {cve_row['patched_version_date']}")
        print(f"Parent version: {rq3_row['parent_version']}")
        print(f"Patched version: {cve_row['patched_version']}")

        # Create unique key for this target_dependency + parent + CVE combination
        unique_key = (
            rq3_row["target_dependency"],
            rq3_row["parent_artifact-group"],
            cve_row["cve_id"],
        )

        # Check if release date is after CVE publish date
        if rq3_row["target_dependent_release_date"] > cve_row["patched_version_date"]:
            try:
                # Clean version strings to just semver numbers and remove trailing .0
                parent_version_str = re.sub(
                    r"[^0-9.]", "", rq3_row["parent_version"]
                ).rstrip(".0")
                patched_version_str = re.sub(
                    r"[^0-9.]", "", cve_row["patched_version"]
                ).rstrip(".0")

                # Compare versions using packaging.version
                parent_ver = version.parse(parent_version_str)
                patched_ver = version.parse(patched_version_str)

                # Only include if parent version is >= patched version
                if parent_ver >= patched_ver:
                    print("Found matching version!")
                    # Calculate days to patch
                    days_to_patch = (
                        rq3_row["target_dependent_release_date"]
                        - cve_row["cve_publish_date"]
                    ).days

                    # Create new row with all requested fields
                    new_row = {
                        "target_dependency": rq3_row["target_dependency"],
                        "parent_artifact-group": rq3_row["parent_artifact-group"],
                        "parent_version": rq3_row["parent_version"],
                        "target_dependent_version": rq3_row["target_dependent_version"],
                        "target_dependent_release_timestamp": rq3_row[
                            "target_dependent_release_timestamp"
                        ],
                        "target_dependent_release_date": rq3_row[
                            "target_dependent_release_date"
                        ],
                        "cve_patched": True,
                        "cve_publish_date": cve_row["cve_publish_date"],
                        "patched_version_date": cve_row["patched_version_date"],
                        "cve_id": cve_row["cve_id"],
                        "severity": cve_row["severity"],
                        "start_version": cve_row["start_version"],
                        "start_version_date": cve_row["start_version_date"],
                        "end_version": cve_row["end_version"],
                        "end_version_date": cve_row["end_version_date"],
                        "patched_version": cve_row["patched_version"],
                        "days_to_patch": days_to_patch,
                    }

                    # Update min version if this is first or lower version for this key
                    if unique_key not in min_versions or parent_ver < version.parse(
                        min_versions[unique_key]["parent_version"].replace(
                            ".RELEASE", ""
                        )
                    ):
                        min_versions[unique_key] = new_row

            except version.InvalidVersion as e:
                print(f"Version parsing error: {e}")
                continue

# Add minimum versions to matching rows
print(f"\nTotal matches found: {len(min_versions)}")
matching_rows = list(min_versions.values())

# Create DataFrame from matching rows
result_df = pd.DataFrame(matching_rows)
print("\nFirst few rows of result:")
print(result_df.head())
result_df = result_df.sort_values(["parent_artifact-group", "patched_version_date"])

# Save to CSV
result_df.to_csv("data/rq3_6_time_to_respond.csv", index=False)
