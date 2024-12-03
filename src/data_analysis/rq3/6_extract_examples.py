import pandas as pd
import numpy as np
from scipy import stats

# Read the data
df = pd.read_csv("data/rq3_results_class_split.csv")

# Convert dates to datetime with UTC timezone
date_columns = ["cve_publish_date", "cve_patch_date", "patched_date", "affected_date"]
for col in date_columns:
    df[col] = pd.to_datetime(df[col], utc=True)


# Classify each row based on date comparisons
def classify_row(row):
    if (
        row["cve_publish_date"] < row["cve_patch_date"]
        and row["cve_patch_date"] < row["patched_date"]
    ):
        return "slow_patch"
    elif (
        row["cve_patch_date"] < row["patched_date"]
        and row["patched_date"] < row["cve_publish_date"]
    ):
        return "fast_adoption"
    elif (
        row["cve_patch_date"] < row["cve_publish_date"]
        and row["cve_publish_date"] < row["patched_date"]
    ):
        return "fast_patch"
    else:
        return "other_type"


df["data_class"] = df.apply(classify_row, axis=1)

# Calculate days between CVE publish date and patched date
df["days_to_patch"] = (df["patched_date"] - df["cve_publish_date"]).dt.days

# Export the enhanced dataset with days_to_patch and data_class
df.to_csv("data/rq3_results_with_days.csv", index=False)
