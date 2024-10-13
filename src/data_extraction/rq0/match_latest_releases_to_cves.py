import pandas as pd

# Read the datasets into pandas DataFrames
latest_releases_cves = pd.read_csv("data/latest_release_cves.csv")
latest_releases = pd.read_csv("data/latest_releases.csv")

# Ensure consistent data types and formatting
latest_releases_cves["release_version"] = (
    latest_releases_cves["release_version"].astype(str).str.strip()
)
latest_releases["Release Version"] = (
    latest_releases["Release Version"].astype(str).str.strip()
)
latest_releases_cves["artifact_name"] = latest_releases_cves[
    "artifact_name"
].str.strip()
latest_releases["Artifact ID"] = latest_releases["Artifact ID"].str.strip()

# Create a composite key in both DataFrames for matching
latest_releases_cves["artifact_version"] = (
    latest_releases_cves["artifact_name"]
    + ":"
    + latest_releases_cves["release_version"]
)
latest_releases["artifact_version"] = (
    latest_releases["Artifact ID"] + ":" + latest_releases["Release Version"]
)

# Add a boolean column indicating existence based on both artifact_name and release_version
latest_releases_cves["Exists_in_latest_releases"] = latest_releases_cves[
    "artifact_version"
].isin(latest_releases["artifact_version"])

# Optionally, you can drop the temporary 'artifact_version' column if you don't need it
latest_releases_cves.drop("artifact_version", axis=1, inplace=True)

# Save the DataFrame with the new column
latest_releases_cves.to_csv("data/latest_releases_cves_with_existence.csv", index=False)
