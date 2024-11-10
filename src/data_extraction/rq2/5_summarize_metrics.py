import os
import pandas as pd

# Get all subdirectories in data/rq2_opendigger
repo_dirs = [
    d
    for d in os.listdir("data/rq2_opendigger")
    if os.path.isdir(os.path.join("data/rq2_opendigger", d))
]

# List of metrics files we're looking for
metrics = [
    f"{value}.csv"
    for value in [
        "issues_new",
        "issues_closed",
        "issue_comments",
        "issue_response_time",
        "issue_resolution_duration",
        "issue_age",
        "code_change_lines_add",
        "code_change_lines_remove",
        "code_change_lines_sum",
        "change_requests",
        "change_requests_accepted",
        "change_requests_reviews",
        "change_request_response_time",
        "change_request_resolution_duration",
        "change_request_age",
        "bus_factor",
        "inactive_contributors",
        "activity",
        "new_contributors",
        "attention",
        "stars",
        "technical_fork",
        "participants",
        "openrank",
    ]
]

# Create empty dataframe
df = pd.DataFrame(index=repo_dirs, columns=metrics)

# For each repository directory
for repo in repo_dirs:
    repo_path = os.path.join("data/rq2_opendigger", repo)

    # Check each metric file
    for metric in metrics:
        if os.path.exists(os.path.join(repo_path, metric)):
            df.loc[repo, metric] = 1
        else:
            df.loc[repo, metric] = None

# Save results
df.to_csv("data/rq2_5_metrics_availability.csv")
