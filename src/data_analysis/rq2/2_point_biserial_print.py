import pandas as pd
import numpy as np
from scipy import stats

# Flag to filter by stars
FILTER_BY_STARS = False
MIN_STARS = 1000

# Read data and setup metrics
df_cve = pd.read_csv("data/rq2_9_trimmed_enriched.csv")
df_non_cve = pd.read_csv("data/rq2_18_trimmed_enriched.csv")

# Rename columns ending in _acc to _acm
for df in [df_cve, df_non_cve]:
    df.columns = [
        col[:-4] + "_acm" if col.endswith("_acc") else col for col in df.columns
    ]

# Filter by stars if flag is enabled
if FILTER_BY_STARS:
    df_cve = df_cve[df_cve["stars_acc"] >= MIN_STARS]
    df_non_cve = df_non_cve[df_non_cve["stars_acc"] >= MIN_STARS]

metrics = [
    "issues_new_acm",
    "issues_closed_acm",
    "issue_comments_acm",
    "code_change_lines_add_acm",
    "code_change_lines_remove_acm",
    "code_change_lines_sum_acm",
    "change_requests_acm",
    "change_requests_accepted_acm",
    "change_requests_reviews_acm",
    "bus_factor_acm",
    "inactive_contributors_acm",
    "activity_acm",
    "new_contributors_acm",
    "attention_acm",
    "stars_acm",
    "technical_fork_acm",
    "participants_acm",
    "openrank_acm",
]

# Bootstrap correlations
n_iterations = 10000
num_cve_samples = len(df_cve)
results = []

for metric in metrics:
    correlations = []
    p_values = []

    for i in range(n_iterations):
        df_non_cve_sampled = df_non_cve.sample(
            n=num_cve_samples, random_state=np.random.randint(0, 1000000000)
        )
        df_cve["cve"], df_non_cve_sampled["cve"] = 1, 0
        df = pd.concat([df_cve, df_non_cve_sampled])

        correlation, p_value = stats.pointbiserialr(df["cve"], df[metric])
        correlations.append(correlation)
        p_values.append(p_value)

    mean_correlation = np.mean(correlations)
    mean_p_value = np.mean(p_values)
    ci_lower = np.percentile(correlations, 2.5)
    ci_upper = np.percentile(correlations, 97.5)

    results.append(
        {
            "Metric": " ".join(
                word.capitalize()
                for word in metric.replace("_acm", "").replace("_", " ").split()
            ),
            "Correlation": f"{mean_correlation:.3f}",
            "P-Value": f"{mean_p_value:.3f}",
            "CI Lower": f"{ci_lower:.3f}",
            "CI Upper": f"{ci_upper:.3f}",
        }
    )

# Sort results by absolute correlation value
results.sort(key=lambda x: abs(float(x["Correlation"])), reverse=True)

# Create and display table
results_df = pd.DataFrame(results)
print("\nPoint-Biserial Correlation Results:")
print("====================================")
print(results_df.to_string(index=False))

# Save to CSV
results_df.to_csv("data/rq2_correlation_results.csv", index=False)
