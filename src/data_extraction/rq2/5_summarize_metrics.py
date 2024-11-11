import os
import pandas as pd
from ...utils.config import OPENDIGGER_VALUES

# Get all subdirectories in data/rq2_opendigger
repo_dirs = [
    d
    for d in os.listdir("data/rq2_opendigger")
    if os.path.isdir(os.path.join("data/rq2_opendigger", d))
]

# Read original repo names from file
with open("data/rq2_3_repo_names.csv") as f:
    original_names = [line.strip() for line in f.readlines()]

# Create mapping from underscore to original names
name_mapping = {name.replace("/", "_"): name for name in original_names}

# List of metrics files we're looking for
metrics = [f"{value}.csv" for value in OPENDIGGER_VALUES]

# Create empty dataframe with original repo names as index
df = pd.DataFrame(index=[name_mapping[d] for d in repo_dirs], columns=metrics)

# For each repository directory
for repo in repo_dirs:
    repo_path = os.path.join("data/rq2_opendigger", repo)
    original_name = name_mapping[repo]

    # Check each metric file
    for metric in metrics:
        if os.path.exists(os.path.join(repo_path, metric)):
            df.loc[original_name, metric] = 1
        else:
            df.loc[original_name, metric] = None

# Save results
df.to_csv("data/rq2_5_metrics_availability.csv")
