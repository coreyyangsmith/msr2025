import pandas as pd
import numpy as np

from ...utils.config import RQ2_15_INPUT, RQ2_15_OUTPUT

# Read the metrics availability data
df = pd.read_csv(RQ2_15_INPUT, index_col=0)

# Print summary statistics
print("\nDataset Summary:")
print("-" * 50)
print(f"Total number of repositories: {len(df)}")
print(f"Total number of metrics: {len(df.columns)}")
print("\nNull values per metric:")
print("-" * 50)
for col in df.columns:
    null_count = df[col].isna().sum()
    if null_count > 0:
        print(f"{col}: {null_count} nulls")

# Count repositories with complete data
complete_repos = df.dropna()
print(f"\nRepositories with complete data: {len(complete_repos)} out of {len(df)}")

# Drop rows with any null values and save just the repo names
df_cleaned = df.dropna()
df_cleaned.index.to_series().to_csv(RQ2_15_OUTPUT, header=False, index=False)
print(
    f"\nSaved cleaned dataset with {len(df_cleaned)} repositories to rq2_15_cleaned_metrics_repos.csv"
)
