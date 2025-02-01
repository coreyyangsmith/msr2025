import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns


def rank_biserial(x, group):
    """
    Computes the rank biserial correlation between a continuous variable `x`
    and a binary grouping variable `group`.

    Parameters:
        x (array-like): Continuous data values.
        group (array-like): Binary group labels (e.g., 0 and 1).

    Returns:
        r_rb (float): The rank biserial correlation.
    """
    # Ensure the inputs are NumPy arrays
    x = np.asarray(x)
    group = np.asarray(group)

    # Split the continuous data based on the binary group labels
    group1 = x[group == 1]
    group0 = x[group == 0]

    n1 = len(group1)
    n0 = len(group0)

    if n1 == 0 or n0 == 0:
        raise ValueError("Both groups must contain at least one observation.")

    # Compute the Mann–Whitney U statistic.
    # Here, U is computed for group1 relative to group0.
    result = stats.mannwhitneyu(group1, group0, alternative="two-sided")
    U1 = result.statistic

    # Calculate rank biserial correlation:
    # This gives a value between -1 and 1.
    r_rb = (2 * U1) / (n1 * n0) - 1

    return r_rb


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

    print("Rank Biserial Correlation Results:")
    print("-" * 50)

    # Create binary labels (1 for CVE, 0 for non-CVE)
    df_cve["cve"] = 1
    df_non_cve["cve"] = 0
    df = pd.concat([df_cve, df_non_cve])

    # Store results for plotting
    results = []

    for metric in metrics:
        # Compute rank biserial correlation
        r_rb = rank_biserial(df[metric], df["cve"])

        # Perform Mann-Whitney U test
        group1 = df[df["cve"] == 1][metric]
        group0 = df[df["cve"] == 0][metric]
        mw_result = stats.mannwhitneyu(group1, group0, alternative="two-sided")

        print(f"\n{metric}:")
        print(f"Rank Biserial Correlation: {r_rb:.3f}")
        print(f"Mann-Whitney U p-value: {mw_result.pvalue:.3e}")

        # Store results
        results.append(
            {
                "metric": metric.replace("_acc", "").replace("_", " ").title(),
                "correlation": r_rb,
                "p_value": mw_result.pvalue,
            }
        )

    # Create DataFrame and sort by correlation strength
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values("correlation", ascending=True)

    # Create the plot
    plt.figure(figsize=(10, 12))

    # Plot correlations
    plt.barh(
        range(len(results_df)), results_df["correlation"], color="#e74c3c", alpha=0.7
    )

    # Add zero line and confidence regions
    plt.axvline(x=0, color="#7f8c8d", linestyle="-", linewidth=1.2, alpha=0.6)
    plt.axvspan(-0.1, 0.1, color="gray", alpha=0.1)  # Weak correlation region

    # Customize the plot
    plt.xlabel("Rank Biserial Correlation Coefficient", fontsize=14, labelpad=10)
    plt.grid(True, axis="x", linestyle="--", alpha=0.4)
    plt.grid(False, axis="y")
    plt.yticks(range(len(results_df)), results_df["metric"], fontsize=12)

    # Add significance markers
    significant_mask = results_df["p_value"] < 0.05
    for i, is_significant in enumerate(significant_mask):
        if is_significant:
            plt.text(
                max(results_df["correlation"]) + 0.02, i, "*", fontsize=14, va="center"
            )

    plt.tight_layout()
    plt.savefig(
        "data/rq2_rank_biserial_correlation.pdf",
        dpi=600,
        bbox_inches="tight",
        format="pdf",
    )
    plt.show()
