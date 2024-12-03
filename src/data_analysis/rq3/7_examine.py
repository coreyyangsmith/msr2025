import pandas as pd

# Read the data
df = pd.read_csv("data/rq3_results_with_days.csv")

# Filter for fast_adoption class and sort by days_to_patch
fast_adoption_df = df[df["data_class"] == "fast_patch"].sort_values("days_to_patch")

# Display first few rows
print("\nFast Adoption Cases (Sorted by Days to Patch):")
print(fast_adoption_df.head())
