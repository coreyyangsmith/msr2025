import pandas as pd

# Read the CSV files
rq3_3_df = pd.read_csv("data/rq3_3_release_dependencies_both.csv")
rq0_4_df = pd.read_csv("data/rq0_4_unique_cves.csv")

# Select and rename columns from rq3_3
rq3_3_selected = rq3_3_df[
    [
        "dependent_artifact_id",
        "affected_parent_artifact_id",
        "affected_parent_version",
        "affected_dependent_version",
        "affected_date",
        "patched_parent_version",
        "patched_dependent_version",
        "patched_date",
        "cve_id",
    ]
]

# Select and rename columns from rq0_4
rq0_4_selected = rq0_4_df[
    [
        "combined_name",
        "cve_id",
        "severity",
        "cve_patched",
        "cve_publish_date",
        "patched_version_date",
    ]
].rename(columns={"patched_version_date": "cve_patch_date"})

# Join the dataframes
merged_df = pd.merge(
    rq3_3_selected,
    rq0_4_selected,
    left_on=["affected_parent_artifact_id", "cve_id"],
    right_on=["combined_name", "cve_id"],
    how="inner",
)

# Drop redundant column
merged_df = merged_df.drop("combined_name", axis=1)

# Convert dates to datetime
merged_df["affected_date"] = pd.to_datetime(merged_df["affected_date"])
merged_df["patched_date"] = pd.to_datetime(merged_df["patched_date"])
merged_df["cve_patch_date"] = pd.to_datetime(merged_df["cve_patch_date"])

# Filter invalid dates and print count
invalid_dates_affected = merged_df[
    merged_df["affected_date"] > merged_df["patched_date"]
]
print(
    f"Number of entries where affected date is later than patched date: {len(invalid_dates_affected)}"
)

invalid_dates_cve = merged_df[merged_df["patched_date"] < merged_df["cve_patch_date"]]
print(
    f"Number of entries where patched date is earlier than CVE patch date: {len(invalid_dates_cve)}"
)

# Remove invalid dates and export
merged_df = merged_df[
    (merged_df["affected_date"] <= merged_df["patched_date"])
    & (merged_df["patched_date"] >= merged_df["cve_patch_date"])
]
merged_df.to_csv("data/rq3_results_class_split.csv", index=False)
