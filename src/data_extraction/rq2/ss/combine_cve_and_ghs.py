import pandas as pd

path1 = "data/filtered_enriched_gh_artifacts.csv"
path2 = "data/cve_lifetimes_updated.csv"

# Load the CSV files
df1 = pd.read_csv(path1)
df2 = pd.read_csv(path2)

# Get the list of unique 'repo' IDs from df1
df1["Artifact"] = df1["group"] + ":" + df1["name"]
repo_ids = df1["Artifact"].unique()

# Filter df2 to only include rows with matching 'repo' IDs
df2_filtered = df2[df2["Artifact"].isin(repo_ids)]

# Merge the DataFrames on 'repo'
final_df = pd.merge(df1, df2_filtered, on="Artifact", how="left")

# Save the final dataset to a CSV file (optional)
final_df.to_csv("data/final_dataset.csv", index=False)

# Display the first few rows of the final dataset
print(final_df.head())
