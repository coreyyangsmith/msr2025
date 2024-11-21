import pandas as pd

"""
This script merges two datasets to enrich dependency data with GitHub repository information.

Steps:
1. Reads two input CSV files:
   - `rq3_2_unique_dependents.csv`: Contains dependency relationships.
   - `rq2_7_combined_datasets.csv`: Contains additional metadata, including GitHub repository details.
2. Merges the datasets on the `parent` column from `rq3_2_unique_dependents.csv` and the `combined_name` column from `rq2_7_combined_datasets.csv` using a left join.
3. Drops the duplicate `combined_name` column after the merge.
4. Saves the enriched dataset to a new CSV file (`rq3_4_combined.csv`).

Dependencies:
- pandas

Usage:
Run this script after generating the `rq3_2_unique_dependents.csv` and `rq2_7_combined_datasets.csv` files.
Ensure the input files are correctly located in the `data/` directory.

Output:
- `rq3_4_combined.csv`: Contains the merged data with dependency relationships and corresponding GitHub repository details.
"""


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
