import pandas as pd

# Read the CSV file into a DataFrame
df = pd.read_csv("data/artifacts_with_cves.csv")

# Select the first column
first_column = df.iloc[:, [0]]  # Using double brackets to keep it as a DataFrame

# Write the first column to a new CSV file
first_column.to_csv("data/artifacts_only_cves.csv", index=False)
