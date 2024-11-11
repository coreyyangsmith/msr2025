import pandas as pd
from ...utils.config import RQ2_7_OUTPUT, RQ2_7_INPUT_METRICS, RQ2_7_INPUT_CVES

# Load datasets
metrics_repos = pd.read_csv(RQ2_7_INPUT_METRICS, header=None, names=["full_name"])
cve_repos = pd.read_csv(RQ2_7_INPUT_CVES)

metrics_repos[["github_owner", "github_repo"]] = metrics_repos["full_name"].str.split(
    "/", expand=True
)

# Find matching rows
merged_df = pd.merge(
    metrics_repos,
    cve_repos,
    left_on=["github_owner", "github_repo"],
    right_on=["github_owner", "github_repo"],
    how="inner",
)

# Add patched_release_id column
merged_df["patched_release_id"] = (
    merged_df["combined_name"] + ":" + merged_df["patched_version"]
)

# Export results
merged_df.to_csv(RQ2_7_OUTPUT, index=False)

print(f"Found {len(merged_df)} matching repositories")
