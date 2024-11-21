import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
import numpy as np

# Read in both datasets
df_cve = pd.read_csv("data/rq2_9_trimmed_enriched.csv")
df_non_cve = pd.read_csv("data/rq2_18_trimmed_enriched.csv")

# List of metrics to correlate with CVE
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

# Get number of CVE samples
num_cve_samples = len(df_cve)

# Number of bootstrap iterations
n_iterations = 1000
bootstrap_correlations = {metric: [] for metric in metrics}

# Perform bootstrap sampling
for i in range(n_iterations):
    # Randomly sample equal number from non-CVE dataset with different random state each time
    random_state = np.random.randint(0, 1000000)
    df_non_cve_sampled = df_non_cve.sample(n=num_cve_samples, random_state=random_state)

    # Add CVE labels
    df_cve["cve"] = 1
    df_non_cve_sampled["cve"] = 0

    # Combine datasets
    df = pd.concat([df_cve, df_non_cve_sampled])

    # Calculate point-biserial correlation between CVE and each metric
    for metric in metrics:
        correlation, _ = stats.pointbiserialr(df["cve"], df[metric])
        bootstrap_correlations[metric].append(correlation)

# Sort metrics by mean correlation
sorted_metrics = sorted(
    metrics, key=lambda m: np.mean(bootstrap_correlations[m]), reverse=True
)

# Create the figure
plt.figure(figsize=(12, 6))

# Prepare data for plotting
plot_data = []
labels = []
for metric in sorted_metrics:
    correlations = bootstrap_correlations[metric]
    plot_data.append(correlations)
    labels.append(metric.replace("_acc", "").replace("_", " ").title())

# Set style
plt.style.use("seaborn")
plt.figure(figsize=(12, 8))

# Create box plot with custom styling
bp = plt.boxplot(
    plot_data,
    labels=labels,
    vert=False,
    patch_artist=True,
    flierprops={
        "marker": "o",
        "markerfacecolor": "#FF6B6B",
        "markeredgecolor": "#FF6B6B",
        "alpha": 0.5,
    },
    boxprops={"facecolor": "#4ECDC4", "alpha": 0.7},
    medianprops={"color": "#2C3E50", "linewidth": 1.5},
    whiskerprops={"color": "#2C3E50"},
    capprops={"color": "#2C3E50"},
)

# Add mean correlation points
means = [np.mean(bootstrap_correlations[m]) for m in sorted_metrics]
plt.plot(
    means,
    range(1, len(sorted_metrics) + 1),
    marker="D",
    color="#E74C3C",
    markersize=8,
    label="Mean",
    linestyle="none",
)

plt.title(
    "Distribution of Correlation Coefficients\nBetween Repository Metrics and CVE Presence",
    fontsize=14,
    pad=20,
)
plt.xlabel("Point-Biserial Correlation Coefficient", fontsize=12, labelpad=10)

# Customize grid
plt.grid(True, axis="x", linestyle="--", alpha=0.7)

# Rotate and align the tick labels so they look better
plt.yticks(range(1, len(labels) + 1), labels, fontsize=10)

# Add legend with custom styling
plt.legend(loc="lower right", frameon=True, framealpha=0.9)

# Add a light vertical line at x=0 for reference
plt.axvline(x=0, color="gray", linestyle="-", linewidth=0.5, alpha=0.5)

plt.tight_layout()
plt.show()
