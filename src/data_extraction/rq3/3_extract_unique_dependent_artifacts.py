import pandas as pd
from collections import defaultdict

"""
This script analyzes and deduplicates dependency relationships between software artifacts. It performs the following tasks:

1. Reads a CSV file containing dependency relationships (`rq3_2_dependent_artifacts.csv`).
2. Removes duplicate entries based on parent-dependent artifact pairs.
3. Constructs a mapping of parent artifacts to their dependent artifacts using a dictionary.
4. Calculates statistics, including:
   - The number of unique parent artifacts.
   - The average number of dependents per parent artifact.
5. Creates a unique list of parent-dependent relationships and saves the results to a new CSV file (`rq3_3_unique_dependencies.csv`).
6. Outputs additional statistics, such as the total number of unique dependent artifacts.

Dependencies:
- pandas
- collections.defaultdict

Usage:
Run this script after generating the input CSV file from previous dependency relationship analysis (e.g., `rq3_2_dependent_artifacts.csv`).
"""


print("\nExtracting unique dependent artifacts...")

# Read the CSV file
df = pd.read_csv("data/rq3_2_dependent_artifacts.csv")
print(f"Read {len(df)} total dependency relationships")

# Create combined name columns if they don't exist
df["dependent_combined_name"] = df["dependentGroupId"] + ":" + df["dependentArtifactId"]

# Remove duplicate parent-dependent pairs
df = df.drop_duplicates(subset=["parent_combined_name", "dependent_combined_name"])
print(f"Found {len(df)} unique parent-dependent pairs")

# Create a dictionary to store parent -> dependent mapping
parent_dependents = defaultdict(set)

# Populate the mapping
for _, row in df.iterrows():
    parent = row["parent_combined_name"].strip().lower()  # Example: Normalize data
    dependent = row["dependent_combined_name"].strip().lower()
    parent_dependents[parent].add(dependent)

print(f"\nFound {len(parent_dependents)} unique parent artifacts")

# Calculate average dependents per parent
total_dependents = sum(len(deps) for deps in parent_dependents.values())
avg_dependents = total_dependents / len(parent_dependents)
print(f"Average dependents per parent: {avg_dependents:.2f}")

# Create list of unique rows for output CSV
rows = [
    {"parent": parent, "dependent": dependent}
    for parent, dependents in parent_dependents.items()
    for dependent in dependents
]

# Convert to dataframe
output_df = pd.DataFrame(rows)

# Final check to ensure all combinations are unique
output_df = output_df.drop_duplicates()

# Write to CSV
output_df.to_csv("data/rq3_3_unique_dependencies.csv", index=False)

print(f"\nWrote {len(output_df)} unique parent-dependent relationships to CSV")
print(f"Found {len(output_df['dependent'].unique())} unique dependent artifacts")
