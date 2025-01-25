import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
import numpy as np
import seaborn as sns

# Set style for publication-quality plot
plt.style.use("seaborn-v0_8-paper")
sns.set_palette("colorblind")

# Flag to filter by stars
FILTER_BY_STARS = False
MIN_STARS = 10000

# Read data and setup metrics
# Read data and rename accumulated metrics columns
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
n_iterations, num_cve_samples = (
    10000,
    len(df_cve),
)  # Increased iterations for more robust results
bootstrap_correlations = {metric: [] for metric in metrics}
for i in range(n_iterations):
    df_non_cve_sampled = df_non_cve.sample(
        n=num_cve_samples, random_state=np.random.randint(0, 1000000000)
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
        word.capitalize() for word in m.replace("_acm", "").replace("_", " ").split()
    )
    for m in sorted_metrics
]

# Create publication-quality figure
plt.figure(figsize=(12, 8))
bp = plt.boxplot(
    plot_data,
    labels=labels,
    vert=False,
    patch_artist=True,
    flierprops={
        "marker": "o",
        "markerfacecolor": "#2C3E50",
        "markeredgecolor": "#2C3E50",
        "alpha": 0.4,
        "markersize": 4,
    },
    boxprops={
        "facecolor": "#3498db",
        "alpha": 0.7,
        "edgecolor": "#2C3E50",
        "linewidth": 1.5,
    },
    medianprops={"color": "#2C3E50", "linewidth": 2},
    whiskerprops={"color": "#2C3E50", "linewidth": 1.5},
    capprops={"color": "#2C3E50", "linewidth": 1.5},
)

# Add mean points with enhanced styling
means = [np.mean(bootstrap_correlations[m]) for m in sorted_metrics]
plt.plot(
    means,
    range(1, len(sorted_metrics) + 1),
    marker="D",
    color="#e74c3c",
    markersize=8,
    label="Mean",
    linestyle="none",
    alpha=0.9,
)

# Enhanced styling
# plt.title(
#     "Correlation between GitHub Repository Metrics and CVE Presence",
#     fontsize=16,
#     pad=20,
#     fontweight="bold",
# )
plt.xlabel("Point-Biserial Correlation Coefficient", fontsize=14, labelpad=10)
plt.grid(True, axis="x", linestyle="--", alpha=0.4)
plt.grid(False, axis="y")
plt.yticks(
    range(1, len(labels) + 1),
    labels,
    fontsize=12,
    fontweight="medium",
)
plt.xticks(fontsize=12)
plt.legend(
    loc="upper right",
    frameon=True,
    framealpha=0.95,
    fontsize=12,
    edgecolor="black",
)

# Add zero line and confidence regions
plt.axvline(x=0, color="#7f8c8d", linestyle="-", linewidth=1.2, alpha=0.6)
plt.axvspan(-0.1, 0.1, color="gray", alpha=0.1)  # Weak correlation region

# Adjust layout and save
plt.xlim(min(min(plot_data)) - 0.05, max(max(plot_data)) + 0.05)
plt.tight_layout()
plt.savefig(
    "data/rq2_correlation_boxplot.png",
    dpi=600,  # Higher DPI for publication quality
    bbox_inches="tight",
    format="pdf",  # Save as PDF for vector graphics
)
plt.show()
