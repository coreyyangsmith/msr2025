import pandas as pd

df = pd.read_csv("data/rq0_3_releases_cves.csv")
unique_cves_per_artifact = df.groupby("combined_name")["cve_id"].nunique()
total_unique_cves = unique_cves_per_artifact.sum()

print("Number of unique CVE IDs per artifact:")
print(unique_cves_per_artifact)
print("\nTotal number of unique CVE IDs across all artifacts:", total_unique_cves)
