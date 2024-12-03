import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# List of metrics to plot
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

# Read the datasets once
df_cve = pd.read_csv("data/rq2_9_trimmed_enriched.csv")
df_non_cve = pd.read_csv("data/rq2_18_trimmed_enriched.csv")

# Set up the plot style
fig = plt.figure(figsize=(20, 25))
fig.suptitle(
    "Distribution of Metrics in CVE vs Non-CVE Repositories", fontsize=16, y=0.95
)

# Create subplots for each metric
for idx, metric in enumerate(metrics, 1):
    ax = plt.subplot(6, 3, idx)

    # Plot histograms with custom styling
    plt.hist(
        df_cve[metric],
        bins=30,
        alpha=0.6,
        color="#FF6B6B",
        label="CVE Repositories",
        density=True,
    )
    plt.hist(
        df_non_cve[metric],
        bins=30,
        alpha=0.6,
        color="#4ECDC4",
        label="Non-CVE Repositories",
        density=True,
    )

    # Clean up metric name for display
    display_name = metric.replace("_acc", "").replace("_", " ").title()

    # Customize subplot appearance
    plt.xlabel(display_name, fontsize=10)
    plt.ylabel("Density", fontsize=10)
    plt.title(display_name, pad=10, fontsize=12)

    # Add legend only if it's the first plot
    if idx == 1:
        plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")

    # Customize ticks
    plt.tick_params(axis="both", which="major", labelsize=8)

    # Add grid with custom styling
    plt.grid(True, linestyle="--", alpha=0.3)

    # Scale y-axis to make distributions more visible
    ax.set_ylim(0, ax.get_ylim()[1] * 1.2)

# Adjust layout to prevent overlap
plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.savefig("metric_distributions.png", dpi=300, bbox_inches="tight")
plt.show()
