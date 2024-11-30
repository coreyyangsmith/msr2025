import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
import numpy as np

# Read data and setup metrics
df_cve = pd.read_csv("data/rq2_9_trimmed_enriched.csv")
df_non_cve = pd.read_csv("data/rq2_18_trimmed_enriched.csv")
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

# Bootstrap correlations
n_iterations, num_cve_samples = 1000, len(df_cve)
bootstrap_correlations = {metric: [] for metric in metrics}
for i in range(n_iterations):
    df_non_cve_sampled = df_non_cve.sample(
        n=num_cve_samples, random_state=np.random.randint(0, 1000000)
    )
    df_cve["cve"], df_non_cve_sampled["cve"] = 1, 0
    df = pd.concat([df_cve, df_non_cve_sampled])
    for metric in metrics:
        correlation, _ = stats.pointbiserialr(df["cve"], df[metric])
        bootstrap_correlations[metric].append(correlation)

# Sort and prepare plot data
sorted_metrics = sorted(
    metrics, key=lambda m: np.mean(bootstrap_correlations[m]), reverse=True
)
plot_data = [bootstrap_correlations[m] for m in sorted_metrics]
labels = [
    " ".join(
        word.capitalize() for word in m.replace("_acc", "").replace("_", " ").split()
    )
    for m in sorted_metrics
]

# Create compressed figure
plt.figure(figsize=(10, 4))
bp = plt.boxplot(
    plot_data,
    labels=labels,
    vert=False,
    patch_artist=True,
    flierprops={
        "marker": ".",
        "markerfacecolor": "#2C3E50",
        "markeredgecolor": "#2C3E50",
        "alpha": 0.3,
        "markersize": 3,
    },
    boxprops={"facecolor": "#3498db", "alpha": 0.6, "edgecolor": "#2C3E50"},
    medianprops={"color": "#2C3E50", "linewidth": 1.2},
    whiskerprops={"color": "#2C3E50", "linewidth": 1},
    capprops={"color": "#2C3E50", "linewidth": 1},
)

# Add mean points and styling
means = [np.mean(bootstrap_correlations[m]) for m in sorted_metrics]
plt.plot(
    means,
    range(1, len(sorted_metrics) + 1),
    marker="D",
    color="#e74c3c",
    markersize=4,
    label="Mean",
    linestyle="none",
    alpha=0.8,
)
plt.title(
    "Metric Correlations with CVE Presence", fontsize=12, pad=10, fontweight="bold"
)
plt.xlabel("Point-Biserial Correlation", fontsize=10, labelpad=6)
plt.grid(True, axis="x", linestyle="--", alpha=0.3)
plt.grid(False, axis="y")
plt.yticks(range(1, len(labels) + 1), labels, fontsize=7, fontweight="bold")
plt.xticks(fontsize=8)
plt.legend(loc="lower right", frameon=True, framealpha=0.9, fontsize=8)
plt.axvline(x=0, color="#7f8c8d", linestyle="-", linewidth=0.8, alpha=0.5)
plt.xlim(min(min(plot_data)) - 0.02, max(max(plot_data)) + 0.02)
plt.tight_layout()
plt.savefig("data/rq2_correlation_boxplot.png", dpi=300, bbox_inches="tight")
plt.show()
