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
        row["cve_publish_date"] <= row["cve_patch_date"]
        and row["cve_patch_date"] <= row["patched_date"]
    ):
        return "slow_patch"
    elif (
        row["cve_patch_date"] <= row["patched_date"]
        and row["patched_date"] <= row["cve_publish_date"]
    ):
        return "fast_adoption"
    elif (
        row["cve_patch_date"] <= row["cve_publish_date"]
        and row["cve_publish_date"] <= row["patched_date"]
    ):
        return "fast_patch"
    else:
        return "other_type"


df["data_class"] = df.apply(classify_row, axis=1)

# Calculate days between CVE publish date and patched date
df["days_to_patch"] = (df["patched_date"] - df["cve_publish_date"]).dt.days


# Function to calculate statistics
def get_statistics(data):
    return pd.Series(
        {
            "Count": len(data),
            "Min": np.min(data),
            "25th": np.percentile(data, 25),
            "Mean": np.mean(data),
            "Median": np.median(data),
            "75th": np.percentile(data, 75),
            "Max": np.max(data),
            "Std": np.std(data),
        }
    )


# Calculate statistics for each class
stats_df = df.groupby("data_class")["days_to_patch"].apply(get_statistics).round(0)

# Print count and percentage of elements in each group
print("\nNumber and percentage of elements in each class:")
counts = df["data_class"].value_counts()
percentages = df["data_class"].value_counts(normalize=True).mul(100).round(1)
for class_name in counts.index:
    print(f"{class_name}: {counts[class_name]} ({percentages[class_name]}%)")

# Convert to more readable format
stats_df = stats_df.reset_index()
stats_df.columns = ["Data Class", "Statistic", "Value"]

# Pivot table for better presentation
final_table = stats_df.pivot(index="Statistic", columns="Data Class", values="Value")

# Print the table
print("\nTime to Patch Statistics (in days) by Data Class:")
print(final_table.to_string())

# Save to CSV
final_table.to_csv("data/rq3_time_to_patch_statistics.csv")
