import pandas as pd
import matplotlib.pyplot as plt
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("plot_histogram.log"), logging.StreamHandler()],
)

# File paths
INPUT_CSV = "data/releases_with_cves.csv"
OUTPUT_PLOT = "figure.tiff"


def plot_cve_severity_histogram(input_csv, output_plot):
    """
    Reads a CSV file containing CVE data, counts the number of CVEs per severity level,
    and plots a histogram.

    Args:
        input_csv (str): Path to the input CSV file.
        output_plot (str): Path to save the output plot image.
    """
    if not os.path.exists(input_csv):
        logging.error(f"Input CSV file '{input_csv}' does not exist.")
        return

    try:
        # Read the CSV file
        df = pd.read_csv(input_csv)
        logging.info(f"Successfully read '{input_csv}' with {len(df)} records.")
    except Exception as e:
        logging.error(f"Error reading '{input_csv}': {e}")
        return

    # Validate required columns
    required_columns = {"cve_severity"}
    if not required_columns.issubset(df.columns):
        logging.error(
            f"Input CSV must contain the following columns: {required_columns}"
        )
        return

    # Clean and standardize the 'cve_severity' column
    df["cve_severity"] = df["cve_severity"].str.upper().str.strip()

    # Define the severity levels and their order
    severity_levels = ["LOW", "MODERATE", "HIGH", "CRITICAL"]
    severity_labels = [
        "Low Severity",
        "Moderate Severity",
        "High Severity",
        "Critical Severity",
    ]

    # Count the number of CVEs per severity level
    severity_counts = (
        df["cve_severity"].value_counts().reindex(severity_levels, fill_value=0)
    )

    # Mapping for colors based on severity
    color_mapping = {
        "LOW": "#2ecc71",  # Green
        "MODERATE": "#f1c40f",  # Yellow
        "HIGH": "#e67e22",  # Orange
        "CRITICAL": "#e74c3c",  # Red
    }
    colors = [
        color_mapping.get(sev, "#95a5a6") for sev in severity_levels
    ]  # Default to gray

    # Prepare labels and counts for plotting
    plot_labels = [label for label in severity_labels]
    plot_counts = [severity_counts.get(sev, 0) for sev in severity_levels]

    # Create a figure and axis
    fig, ax = plt.subplots(figsize=(10, 6))

    # Create bar chart
    bars = ax.bar(plot_labels, plot_counts, color=colors, edgecolor="black")

    # Add counts on top of each bar
    for bar in bars:
        height = bar.get_height()
        ax.annotate(
            f"{int(height)}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 5),  # 5 points vertical offset
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )

    # Set title and labels
    ax.set_title(
        "CVE Incident Counts by Severity Level", fontsize=16, fontweight="bold"
    )
    ax.set_xlabel("Severity Level", labelpad=10)
    ax.set_ylabel("Number of CVE Incidents", labelpad=10)

    # Add grid for y-axis
    ax.yaxis.grid(True, linestyle="--", which="major", color="grey", alpha=0.5)

    # Adjust layout for better fit
    plt.tight_layout()

    # Save and show the plot
    try:
        plt.savefig(output_plot, bbox_inches="tight", transparent=True, dpi=600)
        logging.info(f"Plot saved successfully as '{output_plot}'.")
    except Exception as e:
        logging.error(f"Error saving plot '{output_plot}': {e}")

    plt.show()


def main():
    logging.info("Starting CVE Severity Histogram Plotting.")
    plot_cve_severity_histogram(INPUT_CSV, OUTPUT_PLOT)
    logging.info("CVE Severity Histogram Plotting completed.")


if __name__ == "__main__":
    main()
