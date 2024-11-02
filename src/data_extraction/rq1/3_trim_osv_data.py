import pandas as pd

# Define the file paths
input_file = "data/rq1_cve_lifetimes_updated.csv"  # Input file path
output_file = "data/rq1_cve_lifetimes_updated_trimmed.csv"  # Output file path

# Define columns to keep
columns_to_keep = [
    "Artifact",
    "CVE_ID",
    "Severity",
    "Start Version",
    "End Version",
    "Start",
    "End",
    "Duration",
    "API_ID",
    "API_Aliases",
    "API_Modified",
    "API_Published",
    "API_Severity",
]

# Read in the file
df = pd.read_csv(input_file)

# Store the original number of rows
original_row_count = len(df)

# Select only the specified columns
df = df[columns_to_keep]

# Drop rows where 'API_Published' is NaN or empty
# First, drop rows with NaN in 'API_Published'
df_before_dropna = len(df)
df = df.dropna(subset=["API_Published"])

# Then, drop rows where 'API_Published' is an empty string after stripping whitespace
df_before_empty_drop = len(df)
df = df[df["API_Published"].astype(str).str.strip() != ""]

# Calculate the total number of rows dropped
rows_after_dropna = len(df)
rows_dropped = original_row_count - rows_after_dropna

# Print the number of rows dropped
print(f"Number of rows dropped due to empty 'API_Published' field: {rows_dropped}")

# Save the resulting DataFrame to a new file
df.to_csv(output_file, index=False)

print(f"Filtered data saved to '{output_file}'.")
