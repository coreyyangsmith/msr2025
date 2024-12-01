import pandas as pd

from ...utils.config import RQ0_BAR_PLOT_CVE_SEVERITY_INPUT


def generate_severity_summary(csv_file_path):
    # Read the CSV file
    try:
        df = pd.read_csv(csv_file_path)
    except FileNotFoundError:
        print(f"Error: The file '{csv_file_path}' was not found.")
        return
    except pd.errors.EmptyDataError:
        print(f"Error: The file '{csv_file_path}' is empty.")
        return
    except pd.errors.ParserError:
        print(f"Error: The file '{csv_file_path}' does not appear to be in CSV format.")
        return

    # Check if 'severity' column exists
    if "severity" not in df.columns:
        print("Error: The CSV file does not contain a 'severity' column.")
        return

    # Define the order of severity levels
    severity_order = ["LOW", "MODERATE", "HIGH", "CRITICAL"]

    # Calculate counts
    severity_counts = (
        df["severity"].value_counts().reindex(severity_order, fill_value=0)
    )

    # Calculate total count
    total = severity_counts.sum()

    # Calculate percentages
    severity_percentages = (severity_counts / total * 100).round(2)

    # Prepare the summary DataFrame
    summary_df = pd.DataFrame(
        {
            "Severity": severity_counts.index,
            "Count": [
                f"{count:,} ({percentage}%)"
                for count, percentage in zip(severity_counts, severity_percentages)
            ],
        }
    )

    # Create a DataFrame for the Total row
    total_df = pd.DataFrame({"Severity": ["Total"], "Count": [f"{total:,} (100.00%)"]})

    # Concatenate the Total row to the summary DataFrame
    summary_df = pd.concat([summary_df, total_df], ignore_index=True)

    # Print the summary table
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    generate_severity_summary(RQ0_BAR_PLOT_CVE_SEVERITY_INPUT)
