import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.lines import Line2D


def spearman_correlation(x, group):
    """
    Computes the Spearman correlation between a continuous variable `x`
    and a binary grouping variable `group`.

    Parameters:
        x (array-like): Continuous data values.
        group (array-like): Binary group labels (e.g., 0 and 1).

    Returns:
        rho (float): The Spearman correlation coefficient.
        p_value (float): The p-value for the correlation.
    """
    # Ensure the inputs are NumPy arrays
    x = np.asarray(x)
    group = np.asarray(group)

    # Compute Spearman correlation
    rho, p_value = stats.spearmanr(x, group)

    return rho, p_value


if __name__ == "__main__":
    # Set style for publication-quality plot
    plt.style.use("seaborn-v0_8-paper")
    sns.set_palette("colorblind")

    # Read in datasets
    df_cve = pd.read_csv("data/rq2_9_trimmed_enriched.csv")
    df_non_cve = pd.read_csv("data/rq2_18_trimmed_enriched.csv")

    # Define metrics to analyze
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

    print("Spearman Correlation Results:")
    print("-" * 50)

    # Create binary labels (1 for CVE, 0 for non-CVE)
    df_cve["cve"] = 1
    df_non_cve["cve"] = 0
    df = pd.concat([df_cve, df_non_cve])

    # Store results for plotting
    results = []

    for metric in metrics:
        # Compute Spearman correlation
        rho, p_value = spearman_correlation(df[metric], df["cve"])

        print(f"\n{metric}:")
        print(f"Spearman Correlation: {rho:.3f}")
        print(f"p-value: {p_value:.3e}")

        # Store results
        results.append(
            {
                "metric": metric.replace("_acc", "").replace("_", " ").title(),
                "correlation": rho,
                "p_value": p_value,
            }
        )

    # Create DataFrame and sort by correlation strength
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values("correlation", ascending=False)

    # Create a publication-quality figure
    plt.figure(figsize=(15, 6.5))

    # Plot correlations as dots
    plt.plot(
        results_df["correlation"],
        range(1, len(results_df) + 1),
        marker="D",
        color="#e74c3c",
        markersize=8,
        label="Correlation",
        linestyle="none",
        alpha=0.9,
    )

    # Add zero line and confidence regions
    plt.axvline(x=0, color="#7f8c8d", linestyle="-", linewidth=1.2, alpha=0.6)
    plt.axvspan(-0.1, 0.1, color="gray", alpha=0.1)  # Weak correlation region
    plt.axvspan(
        0, 0.1, color="gray", alpha=0.1
    )  # Additional highlight for 0-0.1 region

    plt.xlabel(
        "Spearman Correlation Coefficient",
        fontsize=14,
        labelpad=5,
        fontweight="bold",
    )
    plt.grid(True, axis="x", linestyle="--", alpha=0.4)
    plt.grid(False, axis="y")
    plt.yticks(
        range(1, len(results_df) + 1),
        results_df["metric"],
        fontsize=14,
        fontweight="bold",
    )
    plt.xticks(fontsize=14, fontweight="bold")
    plt.legend(
        [Line2D([0], [0], marker="D", color="#e74c3c", linestyle="none", alpha=0.9)],
        ["Correlation"],
        loc="upper right",
        frameon=True,
        framealpha=0.95,
        fontsize=14,
        edgecolor="black",
    )

    # Adjust layout and save the figure
    min_x = min(results_df["correlation"]) - 0.05  # Allow negative correlations
    max_x = max(results_df["correlation"]) + 0.05
    plt.xlim(min_x, max_x)
    plt.tight_layout()
    plt.savefig(
        "data/rq2_spearman_correlation.pdf",
        dpi=600,
        bbox_inches="tight",
        format="pdf",
    )
    plt.show()
