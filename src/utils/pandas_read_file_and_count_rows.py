import pandas as pd

csv_file = "data/rq2_cve_lifetimes_updated.csv"
# csv_file = "data/rq2_filtered_github_artifacts.csv"

df = pd.read_csv(csv_file)
num_rows = len(df)

print(f"The file '{csv_file}' has {num_rows} rows.")
