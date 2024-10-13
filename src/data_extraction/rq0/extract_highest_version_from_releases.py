import pandas as pd
from packaging import version
import re

# Load the data into a pandas DataFrame
df = pd.read_csv("data/releases_with_cves.csv")


# Define a function to parse the version string
def parse_version(v):
    return version.parse(v)


# Function to remove suffixes after the numeric version
def clean_version(v):
    match = re.match(r"^(\d+(\.\d+)*)", v)
    if match:
        return match.group(1)
    else:
        return v  # Return original if no match


def split_version(v):
    # Split on non-numeric characters
    parts = re.split(r"[^\d]+", v)
    # Convert parts to integers
    return [int(p) for p in parts if p.isdigit()]


# Apply the parsing function to create a new column for parsed versions
df["clean_release_version"] = df["release_version"].apply(clean_version)
df["version_parts"] = df["release_version"].apply(split_version)


# Function to compare two version parts
def compare_versions(v1, v2):
    return v1 > v2


# Function to get the maximum version per group
def get_max_version(group):
    return (
        group.loc[group["version_parts"].apply(lambda x: x)]
        .sort_values(by="version_parts", ascending=False)
        .iloc[0]
    )


# Group by 'artifact_name' and apply the max version function
max_versions = (
    df.groupby("artifact_name")
    .apply(lambda group: group.loc[group["version_parts"].map(tuple).idxmax()])
    .reset_index(drop=True)
)

# Drop helper columns if desired
max_versions = max_versions.drop(columns=["version_parts"])

print("\nDataFrame with the latest release_version per artifact_name:")
print(max_versions)

max_versions.to_csv("data/latest_release_cves.csv")
