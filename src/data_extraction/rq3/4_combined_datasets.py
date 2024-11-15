import pandas as pd

# Read the datasets
releases_df = pd.read_csv("data/rq3_2_unique_dependents.csv")
rq2_df = pd.read_csv("data/rq2_7_combined_datasets.csv")

# Merge the dataframes based on parent and combined_name
merged_df = releases_df.merge(
    rq2_df[["combined_name", "github_repo", "github_owner"]],
    left_on="parent",
    right_on="combined_name",
    how="left",
)

# Drop the duplicate combined_name column since it's identical to parent
merged_df = merged_df.drop(columns=["combined_name"])

# Save the results
merged_df.to_csv("data/rq3_4_combined.csv", index=False)
