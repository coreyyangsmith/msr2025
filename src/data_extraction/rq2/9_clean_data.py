import pandas as pd

# Read the enriched data
df = pd.read_csv("data/rq2_8_enriched.csv")

# Count nulls in each column
null_counts = df.isnull().sum()

# Print results
print("\nNull counts per column:")
print(null_counts)

# Print total number of nulls
print(f"\nTotal nulls: {df.isnull().sum().sum()}")
