import pandas as pd
import os
from pathlib import Path
from datetime import datetime
import time
from tqdm import tqdm

from ...utils.config import RQ2_17_INPUT, RQ2_17_OUTPUT, OPENDIGGER_VALUES

# Read the combined dataset from step 7
df = pd.read_csv(
    "data/rq2_15_cleaned_metrics_repos.csv", header=None, names=["full_name"]
)

# List of columns to keep
columns_to_keep = [
    "full_name",
    "issues_new_acc",
    "issues_closed_acc",
    "issue_comments_acc",
    "issue_response_time_acc",
    "issue_resolution_duration_acc",
    "issue_age_acc",
    "code_change_lines_add_acc",
    "code_change_lines_remove_acc",
    "code_change_lines_sum_acc",
    "change_requests_acc",
    "change_requests_accepted_acc",
    "change_requests_reviews_acc",
    "change_request_response_time_acc",
    "change_request_resolution_duration_acc",
    "change_request_age_acc",
    "bus_factor_acc",
    "inactive_contributors_acc",
    "activity_acc",
    "new_contributors_acc",
    "attention_acc",
    "stars_acc",
    "technical_fork_acc",
    "participants_acc",
    "openrank_acc",
]


# Function to get accumulated value for a specific date from a metrics file
def get_accumulated_value(metrics_file, target_date):
    if not os.path.exists(metrics_file):
        return None

    metrics_df = pd.read_csv(metrics_file)
    if metrics_df.empty:
        return None

    try:
        # Convert date strings to datetime for comparison
        metrics_df["Date"] = pd.to_datetime(metrics_df["Date"])
        target_date = pd.to_datetime(target_date)

        # Find exact match or closest date before target_date
        mask = metrics_df["Date"] <= target_date
        if not mask.any():
            return None

        closest_row = metrics_df[mask].iloc[-1]
        return closest_row["Accumulated Value"]

    except pd._libs.tslibs.parsing.DateParseError:
        return None


# List of metrics files to check for each repo
metric_files = [f"{value}.csv" for value in OPENDIGGER_VALUES]

print(f"\nProcessing {len(df)} repositories...")
start_time = time.time()

# Process each repository with progress bar
for idx, row in tqdm(df.iterrows(), total=len(df), desc="Enriching metrics data"):
    repo_name = row["full_name"].replace("/", "_")

    # No CVE, therefore evaluate at current date
    target_date = datetime.now().strftime("%Y-%m-%d")

    # Check each metric file
    for metric_file in metric_files:
        metrics_path = f"data/rq11_opendigger/{repo_name}/{metric_file}"

        # Get accumulated value for target date
        acc_value = get_accumulated_value(metrics_path, target_date)

        # Create column name from metric file (remove .csv)
        metric_name = metric_file.replace(".csv", "")

        # Add to dataframe
        df.at[idx, f"{metric_name}_acc"] = acc_value

elapsed_time = time.time() - start_time
print(f"\nProcessing completed in {elapsed_time:.2f} seconds")

# Keep only specified columns and save enriched dataset
df = df[columns_to_keep]
df.to_csv(RQ2_17_OUTPUT, index=False)
print(f"Enriched dataset saved to {RQ2_17_OUTPUT}")
