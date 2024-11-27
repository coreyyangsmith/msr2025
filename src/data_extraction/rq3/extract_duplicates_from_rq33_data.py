import pandas as pd

# Read the CSV file
df = pd.read_csv("data/rq3_3_unique.csv")

# Keep first occurrence of duplicates and unique entries
unique_entries = df.drop_duplicates(subset=['dependent_artifact_id', 'cve_id'], keep='first')

# Find duplicates for analysis purposes
duplicates = df[df.duplicated(subset=['dependent_artifact_id', 'cve_id'], keep=False)]
duplicates = duplicates.sort_values(['dependent_artifact_id', 'cve_id'])

# Export duplicates for analysis and unique entries for further processing
duplicates.to_csv("data/rq3_3_duplicates.csv", index=False)
unique_entries.to_csv("data/rq3_3_unique.csv", index=False)

print(f"Total entries: {len(df)}")
print(f"Duplicate entries: {len(duplicates)}")
print(f"Unique entries (including one copy of duplicates): {len(unique_entries)}")
print("\nFiles exported:")
print("- data/rq3_3_duplicates.csv")
print("- data/rq3_3_unique.csv")
