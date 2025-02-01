import numpy as np
import pandas as pd
from scipy import stats

# Read in datasets
df_cve = pd.read_csv("data/rq2_9_trimmed_enriched.csv")
df_non_cve = pd.read_csv("data/rq2_18_trimmed_enriched.csv")

# Define metrics to test
metrics = [
    "issues_new_acc",
    "issues_closed_acc",
    "issue_comments_acc",
    "code_change_lines_add_acc",
    "code_change_lines_remove_acc",
    "code_change_lines_sum_acc",
    "change_requests_acc",
    "change_requests_accepted_acc",
    "change_requests_reviews_acc",
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

print("Wilcoxon Rank-Sum Test Results:")
print("-" * 50)

# Perform Wilcoxon rank-sum test for each metric
alpha = 0.05
for metric in metrics:
    # Get data for each group
    cve_data = df_cve[metric].values
    non_cve_data = df_non_cve[metric].values

    # Perform the Wilcoxon rank-sum test
    statistic, p_value = stats.ranksums(cve_data, non_cve_data)

    print(f"\n{metric}:")
    print(f"Test Statistic: {statistic:.3f}")
    print(f"P-Value: {p_value:.3e}")

    # Interpret the result
    if p_value < alpha:
        print("Reject H0: Significant difference between CVE and non-CVE repositories")
    else:
        print(
            "Fail to reject H0: No significant difference between CVE and non-CVE repositories"
        )
