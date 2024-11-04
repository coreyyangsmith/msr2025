import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Define the CSV data as a multi-line string
data_path = "data/artifacts_with_cves.csv"


def calculate_total_cve_counts_by_severity(df: pd.DataFrame):
    # Calculate the total counts per severity level
    severity_totals = df[
        [
            "low_severity_count",
            "medium_severity_count",
            "high_severity_count",
            "critical_severity_count",
            "unknown_severity_count",
        ]
    ].sum()

    print("\nTotal CVE Counts by Severity:")
    print(severity_totals)


def calculate_average_cve_per_artifact(df: pd.DataFrame):
    # Compute the average CVE count per artifact
    average_cve_count = df["cve_count"].mean()
    print(f"\nAverage CVE Count per Artifact: {average_cve_count}")


def show_artifact_with_highest_release_count(df: pd.DataFrame):
    # Find the artifact with the highest release count
    max_release_artifact = df.loc[df["release_count"].idxmax()]

    print("\nArtifact with the Highest Release Count:")
    print(max_release_artifact)


def calculate_percentage_of_releases_with_cve(df: pd.DataFrame):
    # Calculate the percentage of releases with CVEs
    df["percentage_releases_with_cves"] = (
        df["releases_with_cves"] / df["release_count"]
    ) * 100

    print("\nPercentage of Releases with CVEs for Each Artifact:")
    print(df[["artifact_name", "percentage_releases_with_cves"]])


def group_by_severity(df: pd.DataFrame):
    # Melt the DataFrame to group by severity levels
    severity_columns = [
        "low_severity_count",
        "medium_severity_count",
        "high_severity_count",
        "critical_severity_count",
        "unknown_severity_count",
    ]

    melted_df = df.melt(
        id_vars=["artifact_name"],
        value_vars=severity_columns,
        var_name="severity_level",
        value_name="count",
    )

    print("\nData Grouped by Severity Levels:")
    print(melted_df)


def visualize_cve_counts(df: pd.DataFrame):
    # Plot CVE counts per artifact
    plt.figure(figsize=(8, 6))
    plt.bar(df["artifact_name"], df["cve_count"], color="skyblue")
    plt.xlabel("Artifact Name")
    plt.ylabel("CVE Count")
    plt.title("CVE Counts per Artifact")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def visualize_bar_chart_total_severity(df: pd.DataFrame):
    # Calculate the total counts per severity level
    severity_totals = df[
        [
            "low_severity_count",
            "medium_severity_count",
            "high_severity_count",
            "critical_severity_count",
            "unknown_severity_count",
        ]
    ].sum()

    # Plot the total severity counts
    plt.figure(figsize=(8, 6))
    severity_totals.plot(kind="bar", color="skyblue")
    plt.xlabel("Severity Level")
    plt.ylabel("Total CVE Count")
    plt.title("Total CVE Counts by Severity Level")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def visaluze_stacked_bar_severity_count_per_artifact(df: pd.DataFrame):
    # Prepare data for the stacked bar chart
    severity_columns = [
        "low_severity_count",
        "medium_severity_count",
        "high_severity_count",
        "critical_severity_count",
        "unknown_severity_count",
    ]

    # Set the artifact names as the index
    df_severity = df.set_index("artifact_name")

    # Plot the stacked bar chart
    df_severity[severity_columns].plot(kind="bar", stacked=True, figsize=(10, 6))

    plt.xlabel("Artifact Name")
    plt.ylabel("CVE Count")
    plt.title("CVE Severity Distribution per Artifact")
    plt.xticks(rotation=45)
    plt.legend(title="Severity Level", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()
    plt.show()


def visualize_scatter_plot_release_vs_cve(df: pd.DataFrame):
    # Plot scatter plot
    plt.figure(figsize=(8, 6))
    plt.scatter(df["release_count"], df["cve_count"], color="green")

    # Add labels and title
    plt.xlabel("Release Count")
    plt.ylabel("CVE Count")
    plt.title("Release Count vs. CVE Count")
    plt.grid(True)

    # Annotate each point with the artifact name
    for i, txt in enumerate(df["artifact_name"]):
        plt.annotate(
            txt,
            (df["release_count"][i], df["cve_count"][i]),
            textcoords="offset points",
            xytext=(0, 10),
            ha="center",
        )

    plt.tight_layout()
    plt.show()


def visualize_heatmap(df: pd.DataFrame):
    # Prepare data for the heatmap
    heatmap_data = df.pivot_table(index="artifact_name", values="severity_columns")

    # Plot the heatmap
    plt.figure(figsize=(8, 6))
    sns.heatmap(heatmap_data, annot=True, fmt="d", cmap="YlGnBu")

    plt.title("Heatmap of CVE Counts by Severity and Artifact")
    plt.xlabel("Severity Level")
    plt.ylabel("Artifact Name")
    plt.tight_layout()
    plt.show()


# Load the CSV data into a DataFrame
df = pd.read_csv(data_path)
calculate_average_cve_per_artifact(df)
# visualize_cve_counts(df)
# visualize_bar_chart_total_severity(df) # good one
# visaluze_stacked_bar_severity_count_per_artifact(df)
# visualize_scatter_plot_release_vs_cve(df)
visualize_heatmap(df)
