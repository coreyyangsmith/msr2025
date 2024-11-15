import pandas as pd

# Read the input files
all_artifacts_df = pd.read_csv("data/rq0_1_all_artifacts.csv", names=["artifact"])
cve_artifacts_df = pd.read_csv("data/rq0_2_artifacts_cve_releases_count.csv")

# Get list of artifacts that have CVEs
cve_artifact_names = cve_artifacts_df["combined_name"].unique()

# Filter out artifacts that have CVEs

print(all_artifacts_df.head())
non_cve_artifacts = all_artifacts_df[
    ~all_artifacts_df["artifact"].isin(cve_artifact_names)
]

# Export to CSV
non_cve_artifacts.to_csv("data/rq0_2_non_cve_artifacts.csv", index=False)
