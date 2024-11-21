import pandas as pd

# Step 1: Read in the rq2_9 file
df_rq2_9 = pd.read_csv("data/rq2_9_trimmed_enriched.csv")

# Step 2: Extract all metrics (columns)
metrics = df_rq2_9.columns.tolist()
# If specific metrics are needed:
# metrics = ['metric1', 'metric2', 'metric3']
# df_metrics = df_rq2_9[metrics]

# Step 3: Extract number of items
num_items = df_rq2_9.shape[0]
print(f"Number of items in rq2_9: {num_items}")

# Step 4: Read in the rq2_18 file
df_rq2_18 = pd.read_csv("data/rq2_18_trimmed_enriched.csv")

# Step 5: Randomly sample the same number of items from rq2_18
df_sampled = df_rq2_18.sample(n=num_items, random_state=42)

# Step 6: Add CVE column to both dataframes
df_rq2_9["cve"] = 1
df_sampled["cve"] = 0

# Step 7: Combine the datasets
combined_df = pd.concat([df_rq2_9, df_sampled])

# Step 8: Output the combined dataset
combined_df.to_csv("data/rq2_19_combined_final.csv", index=False)
print("Combined dataset with CVE labels saved to 'data/rq2_19_combined_final.csv'")
