import pandas as pd
from ...utils.config import RQ2_16_OUTPUT, RQ2_16_INPUT_METRICS, RQ2_16_INPUT_CVES

# Load datasets
metrics_repos = pd.read_csv(RQ2_16_INPUT_METRICS, header=None, names=["full_name"])
cve_repos = pd.read_csv(RQ2_16_INPUT_CVES)

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

# Export results
merged_df.to_csv(RQ2_16_OUTPUT, index=False)

print(f"Found {len(merged_df)} matching CVE instances")
