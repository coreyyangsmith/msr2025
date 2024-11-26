import pandas as pd

# Read the CSV file
df = pd.read_csv("data/rq3_3_release_dependencies.csv")

# Initialize counters
affected_not_patched = 0
affected_and_patched = 0
patched_not_affected = 0
neither = 0

# For each row, check which category it falls into
for _, row in df.iterrows():
    has_affected = pd.notna(row["affected_parent_artifact_id"]) and pd.notna(
        row["affected_parent_version"]
    )
    has_patched = pd.notna(row["patched_parent_artifact_id"]) and pd.notna(
        row["patched_parent_version"]
    )

    if has_affected and not has_patched:
        affected_not_patched += 1
    elif has_affected and has_patched:
        affected_and_patched += 1
    elif not has_affected and has_patched:
        patched_not_affected += 1
    else:
        neither += 1

print("\nStatistics:")
print(f"Affected but not patched: {affected_not_patched}")
print(f"Both affected and patched: {affected_and_patched}")
print(f"Patched but not affected: {patched_not_affected}")
print(f"Neither affected nor patched: {neither}")
print(f"Total entries: {len(df)}")

# Filter for each category
affected_not_patched_df = df[
    df["affected_parent_artifact_id"].notna()
    & df["affected_parent_version"].notna()
    & df["patched_parent_artifact_id"].isna()
    & df["patched_parent_version"].isna()
]

affected_and_patched_df = df[
    df["affected_parent_artifact_id"].notna()
    & df["affected_parent_version"].notna()
    & df["patched_parent_artifact_id"].notna()
    & df["patched_parent_version"].notna()
]

patched_not_affected_df = df[
    df["affected_parent_artifact_id"].isna()
    & df["affected_parent_version"].isna()
    & df["patched_parent_artifact_id"].notna()
    & df["patched_parent_version"].notna()
]

neither_df = df[
    df["affected_parent_artifact_id"].isna()
    & df["affected_parent_version"].isna()
    & df["patched_parent_artifact_id"].isna()
    & df["patched_parent_version"].isna()
]

# Export to separate CSV files
affected_not_patched_df.to_csv(
    "data/rq3_3_release_dependencies_affected_only.csv", index=False
)
affected_and_patched_df.to_csv("data/rq3_3_release_dependencies_both.csv", index=False)
patched_not_affected_df.to_csv(
    "data/rq3_3_release_dependencies_patched_only.csv", index=False
)
neither_df.to_csv("data/rq3_3_release_dependencies_neither.csv", index=False)
