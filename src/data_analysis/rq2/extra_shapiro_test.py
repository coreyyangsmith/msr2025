import numpy as np
import pandas as pd
from scipy.stats import shapiro

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

# Perform Shapiro-Wilk test for each metric in both datasets
alpha = 0.05
print("Shapiro-Wilk Test Results:")
print("-" * 50)
print("\nCVE Dataset:")
for metric in metrics:
    stat, p_value = shapiro(df_cve[metric])
    print(f"\n{metric}:")
    print(f"Test Statistic: {stat:.3f}")
    print(f"P-Value: {p_value:.3e}")
    print("Normal" if p_value > alpha else "Not normal")

print("\n" + "-" * 50)
print("\nNon-CVE Dataset:")
for metric in metrics:
    stat, p_value = shapiro(df_non_cve[metric])
    print(f"\n{metric}:")
    print(f"Test Statistic: {stat:.3f}")
    print(f"P-Value: {p_value:.3e}")
    print("Normal" if p_value > alpha else "Not normal")
