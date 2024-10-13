import pandas as pd

data = "data/latest_releases_cves_with_existence.csv"

df = pd.read_csv(data)

count_true = df["Exists_in_latest_releases"].sum()

print(f"Number of Latest Releases with CVEs: {count_true}")
