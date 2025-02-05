import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.lines import Line2D

N_BOOTSTRAP = 10000


def rank_biserial_from_groups(group1, group0):
    """
    Computes the rank biserial correlation between two groups of data.

    Parameters:
        group1 (array-like): Continuous data for group 1 (e.g., CVE).
        group0 (array-like): Continuous data for group 0 (e.g., non-CVE).

    Returns:
        r_rb (float): The rank biserial correlation.
    """
    group1 = np.asarray(group1)
    group0 = np.asarray(group0)
    n1 = len(group1)
    n0 = len(group0)

    if n1 == 0 or n0 == 0:
        raise ValueError("Both groups must contain at least one observation.")

    # Compute the Mann–Whitney U statistic (for group1 relative to group0)
    result = stats.mannwhitneyu(group1, group0, alternative="two-sided")
    U1 = result.statistic

    # Calculate rank biserial correlation (value between -1 and 1)
    r_rb = (2 * U1) / (n1 * n0) - 1
    return r_rb


def bootstrap_rank_biserial_from_groups_balanced(
    group1, group0, n_bootstrap=10000, random_state=None
):
    """
    Bootstraps the rank biserial correlation using balanced (or "matched‐sized") sampling.
    For each replicate, we sample (without replacement) the same number of observations
    from each group—the minimum of the two group sizes.

    (Note: For the smaller group a full permutation is used, so every observation appears once.
    For the larger group, a random subset is taken.)

    Parameters:
        group1 (array-like): Continuous data for group 1.
        group0 (array-like): Continuous data for group 0.
        n_bootstrap (int): Number of bootstrap iterations.
        random_state (int or None): Seed for reproducibility.

    Returns:
        boot_corrs (np.ndarray): Array of bootstrapped correlation values.
    """
    group1 = np.asarray(group1)
    group0 = np.asarray(group0)
    n1 = len(group1)
    n0 = len(group0)

    # Use the minimum length between groups for balanced sampling
    n_samples = min(n1, n0)
    print(f"n1: {n1}, n0: {n0}, using n_samples: {n_samples}")

    if n1 == 0 or n0 == 0:
        raise ValueError("Both groups must contain at least one observation.")

    boot_corrs = np.empty(n_bootstrap)
    rng = np.random.default_rng(random_state)

    for i in range(n_bootstrap):
        # For each replicate, take a random permutation and then slice the first n_samples indices.
        indices1 = rng.permutation(n1)[:n_samples]
        indices0 = rng.permutation(n0)[:n_samples]
        sample1 = group1[indices1]
        sample0 = group0[indices0]

        U1 = stats.mannwhitneyu(sample1, sample0, alternative="two-sided").statistic
        boot_corrs[i] = (2 * U1) / (n_samples * n_samples) - 1

    return boot_corrs


if __name__ == "__main__":
    # Set style for publication-quality plots
    plt.style.use("seaborn-v0_8-paper")
    sns.set_palette("colorblind")

    # Read in the segregated datasets
    df_cve = pd.read_csv("data/rq2_9_trimmed_enriched.csv")
    df_non_cve = pd.read_csv("data/rq2_18_trimmed_enriched.csv")

    # Define the metrics to analyze
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

    print("Rank Biserial Correlation Results (with balanced bootstrap 95% CIs):")
    print("-" * 70)

    # Store results for later plotting
    results = []

    for metric in metrics:
        # Extract the metric values for each group
        data_cve = df_cve[metric]
        data_non_cve = df_non_cve[metric]

        # Compute the observed rank biserial correlation
        observed_corr = rank_biserial_from_groups(data_cve, data_non_cve)

        # Perform balanced bootstrap sampling for the correlation
        boot_corrs = bootstrap_rank_biserial_from_groups_balanced(
            data_cve, data_non_cve, n_bootstrap=N_BOOTSTRAP, random_state=42
        )

        # Compute the 95% confidence interval from the bootstrap samples
        ci_lower, ci_upper = np.percentile(boot_corrs, [2.5, 97.5])

        # Perform the Mann–Whitney U test on the original data
        mw_result = stats.mannwhitneyu(data_cve, data_non_cve, alternative="two-sided")

        print(f"\n{metric}:")
        print(f"Observed Rank Biserial Correlation: {observed_corr:.3f}")
        print(f"95% CI: [{ci_lower:.3f}, {ci_upper:.3f}]")
        print(f"Mann–Whitney U p-value: {mw_result.pvalue:.3e}")

        # Save results for plotting; clean up metric names for display
        metric_display = metric.replace("_acc", "").replace("_", " ").title()
        if metric_display == "Bus Factor":
            metric_display = "Contributor Absence Factor"
        elif metric_display == "Change Requestsepted":
            metric_display = "Change Requests Accepted"

        results.append(
            {
                "metric": metric_display,
                "correlations": boot_corrs,
                "p_value": mw_result.pvalue,
            }
        )

    # Sort the results by the mean correlation (in descending order)
    results = sorted(results, key=lambda x: np.mean(x["correlations"]), reverse=True)

    # Prepare data for plotting
    plot_data = [r["correlations"] for r in results]
    labels = [r["metric"] for r in results]

    # Create a publication-quality figure
    plt.figure(figsize=(15, 6.5))
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
    means = [np.mean(r["correlations"]) for r in results]
    plt.plot(
        means,
        range(1, len(results) + 1),
        marker="D",
        color="#e74c3c",
        markersize=8,
        label="Mean",
        linestyle="none",
        alpha=0.9,
    )

    plt.xlabel(
        "Rank Biserial Correlation Coefficient",
        fontsize=14,
        labelpad=5,
        fontweight="bold",
    )
    plt.grid(True, axis="x", linestyle="--", alpha=0.4)
    plt.grid(False, axis="y")
    plt.yticks(
        range(1, len(labels) + 1),
        labels,
        fontsize=14,
        fontweight="bold",
    )
    plt.xticks(fontsize=14, fontweight="bold")
    plt.legend(
        [Line2D([0], [0], marker="D", color="#e74c3c", linestyle="none", alpha=0.9)],
        ["Mean"],
        loc="upper right",
        frameon=True,
        framealpha=0.95,
        fontsize=14,
        edgecolor="black",
    )
    # Add a zero line and a shaded region for weak correlations
    plt.axvline(x=0, color="#7f8c8d", linestyle="-", linewidth=1.2, alpha=0.6)
    plt.axvspan(-0.1, 0.1, color="gray", alpha=0.1)  # Weak correlation region

    # Adjust layout and save the figure
    min_x = np.min([np.min(result["correlations"]) for result in results])
    max_x = np.max([np.max(result["correlations"]) for result in results])
    plt.xlim(min_x - 0.05, max_x + 0.05)
    plt.tight_layout()
    plt.savefig(
        "data/rq2_rank_biserial_correlation_bootstrap.pdf",
        dpi=600,
        bbox_inches="tight",
        format="pdf",
    )
    plt.show()
