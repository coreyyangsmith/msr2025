import pandas as pd

# Specify the input and output file paths
input_file = "data/artifacts_with_cves.csv"
output_file = "data/artifacts_with_unknown_severity.csv"

# Load the CSV file into a DataFrame
try:
    df = pd.read_csv(input_file)
    print(f"Successfully loaded '{input_file}'.")
except FileNotFoundError:
    print(f"Error: The file '{input_file}' does not exist.")
    exit(1)
except pd.errors.EmptyDataError:
    print(f"Error: The file '{input_file}' is empty.")
    exit(1)
except pd.errors.ParserError:
    print(f"Error: The file '{input_file}' does not appear to be in CSV format.")
    exit(1)

# Check if 'unknown_severity_count' column exists
if "unknown_severity_count" not in df.columns:
    print("Error: 'unknown_severity_count' column is missing from the input file.")
    exit(1)

# Filter rows where 'unknown_severity_count' > 0
filtered_df = df[df["unknown_severity_count"] > 0]

# Check if any rows meet the condition
if filtered_df.empty:
    print("No rows found with 'unknown_severity_count' greater than 0.")
else:
    # Save the filtered DataFrame to a new CSV file
    filtered_df.to_csv(output_file, index=False)
    print(f"Filtered data has been saved to '{output_file}'.")
