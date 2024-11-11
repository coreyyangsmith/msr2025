import pandas as pd
from collections import defaultdict

print("\nExtracting unique dependent artifacts...")

# Read the CSV file
df = pd.read_csv("data/rq3_1_dependent_artifacts.csv")
print(f"Read {len(df)} total dependency relationships")

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
output_df.to_csv("data/rq3_2_unique_dependents.csv", index=False)

print(f"\nWrote {len(output_df)} unique parent-dependent relationships to CSV")
print(f"Found {len(output_df['dependent'].unique())} unique dependent artifacts")
