import pandas as pd

# Read the CSV files
df_rq32 = pd.read_csv("data/rq3_2_dependent_artifacts copy.csv")
df_rq33 = pd.read_csv("data/rq3_3_unique.csv")

# Create combined dependent artifact id column for rq32
df_rq32['dependent_artifact_id'] = df_rq32['dependentGroupId'] + ':' + df_rq32['dependentArtifactId']

# Create sets of tuples with the matching criteria for rq33 (affected, patched, and none_found)
rq33_affected_pairs = set(zip(df_rq33['affected_parent_artifact_id'], df_rq33['dependent_artifact_id']))
rq33_patched_pairs = set(zip(df_rq33['patched_parent_artifact_id'], df_rq33['dependent_artifact_id']))
rq33_none_found_pairs = set(zip(df_rq33[df_rq33['none_found'].notna()]['none_found'], 
                               df_rq33[df_rq33['none_found'].notna()]['dependent_artifact_id']))
rq33_pairs = rq33_affected_pairs | rq33_patched_pairs | rq33_none_found_pairs

# Create matching tuples for rq32
rq32_pairs = set(zip(df_rq32['parent_combined_name'], df_rq32['dependent_artifact_id']))

# Find pairs in rq32 that are not in rq33
missing_pairs = rq32_pairs - rq33_pairs

# Filter df_rq32 to only include the missing pairs
missing_df = df_rq32[df_rq32.apply(lambda x: (x['parent_combined_name'], x['dependent_artifact_id']) in missing_pairs, axis=1)]

# Drop the created dependent_artifact_id column
missing_df = missing_df.drop('dependent_artifact_id', axis=1)

# Save to CSV
missing_df.to_csv("data/rq3_2_missing_from_rq3_3.csv", index=False)

print(f"Total entries in RQ3.2: {len(df_rq32)}")
print(f"Total entries in RQ3.3: {len(df_rq33)}")
print(f"Number of entries in RQ3.2 not found in RQ3.3: {len(missing_df)}")
