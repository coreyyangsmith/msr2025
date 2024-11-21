import pandas as pd

# Read the enriched dataset
df = pd.read_csv("data/rq2_17_enriched.csv")

# Columns to remove
columns_to_remove = [
    "issue_response_time_acc",
    "issue_resolution_duration_acc",
    "issue_age_acc",
    "change_request_response_time_acc",
    "change_request_resolution_duration_acc",
    "change_request_age_acc",
]

# Remove specified columns
df = df.drop(columns=columns_to_remove)

# Remove rows with any null values
df = df.dropna()

# Save cleaned dataset
df.to_csv("data/rq2_18_trimmed_enriched.csv", index=False)

print(
    f"\nSaved cleaned dataset with {len(df)} rows to data/rq2_18_trimmed_enriched.csv"
)
