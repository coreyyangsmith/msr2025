import os
import pandas as pd
import time
from ...utils.config import (
    OPENDIGGER_VALUES,
    RQ14_OPENDIGGER_INPUT,
    RQ14_FILE_INPUT,
    RQ14_OUTPUT,
)

print("Starting metrics availability analysis...")
start_time = time.time()

# Get all subdirectories in RQ14_OPENDIGGER_INPUT
repo_dirs = [
    d
    for d in os.listdir(RQ14_OPENDIGGER_INPUT)
    if os.path.isdir(os.path.join(RQ14_OPENDIGGER_INPUT, d))
]
print(f"Found {len(repo_dirs)} repository directories")

with open(RQ14_FILE_INPUT) as f:
    original_names = [line.strip() for line in f.readlines()]
print(f"Read {len(original_names)} original repository names")

# Create mapping from underscore to original names
name_mapping = {name.replace("/", "_"): name for name in original_names}

# List of metrics files we're looking for
metrics = [f"{value}.csv" for value in OPENDIGGER_VALUES]
print(f"Looking for {len(metrics)} metrics files: {metrics}")

# Create empty dataframe with original repo names as index
# Filter out any repo_dirs that aren't in the mapping
valid_repo_dirs = [d for d in repo_dirs if d in name_mapping]
print(f"Found {len(valid_repo_dirs)} valid repositories")

df = pd.DataFrame(index=[name_mapping[d] for d in valid_repo_dirs], columns=metrics)

# For each repository directory
for i, repo in enumerate(valid_repo_dirs, 1):
    if i % 10 == 0:
        print(f"Processing repository {i}/{len(valid_repo_dirs)}")

    repo_path = os.path.join("data/rq11_opendigger", repo)
    original_name = name_mapping[repo]

    # Check each metric file
    metrics_found = 0
    for metric in metrics:
        if os.path.exists(os.path.join(repo_path, metric)):
            df.loc[original_name, metric] = 1
            metrics_found += 1
        else:
            df.loc[original_name, metric] = None

    if metrics_found == 0:
        print(f"Warning: No metrics found for {original_name}")

# Calculate and print metrics availability stats
total_possible = len(valid_repo_dirs) * len(metrics)
total_found = df.count().sum()
print(f"\nMetrics availability statistics:")
print(f"Total possible metrics: {total_possible}")
print(f"Total metrics found: {total_found}")
print(f"Overall availability: {(total_found/total_possible)*100:.1f}%")

# Save results
df.to_csv(RQ14_OUTPUT)
print(f"\nResults saved to {RQ14_OUTPUT}.csv")
print(f"Total time elapsed: {time.time() - start_time:.1f} seconds")
