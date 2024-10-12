import pandas as pd

# Load the CSV file
file_path = "data/enriched_gh_artifacts.csv"  # Replace with your file path
df = pd.read_csv(file_path)

# Drop rows where 'stars', 'forks', 'watchers', and 'downloads' are all zero
df_cleaned = df[
    ~(
        (df["stars"] == 0)
        & (df["forks"] == 0)
        & (df["watchers"] == 0)
        & (df["downloads"] == 0)
    )
]

# Save the cleaned DataFrame to a new CSV file
output_path = (
    "data/filtered_enriched_gh_artifacts.csv"  # Replace with your output file path
)
df_cleaned.to_csv(output_path, index=False)

print(f"Cleaned CSV saved to {output_path}")
