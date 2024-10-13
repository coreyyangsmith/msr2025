import pandas as pd

# Read the CSV file into a DataFrame
df = pd.read_csv("artifacts_with_cves_1.csv")

# Select the first column
first_column = df.iloc[:, [0]]  # Using double brackets to keep it as a DataFrame

# Write the first column to a new CSV file
first_column.to_csv("artifacts_only_cves.csv", index=False)
