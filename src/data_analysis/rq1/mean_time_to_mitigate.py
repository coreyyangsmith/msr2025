import pandas as pd
from datetime import timedelta
import seaborn as sns


import re
import matplotlib.pyplot as plt  # Optional, for visualization


def parse_duration(duration_str):
    """
    Parses a duration string formatted as "X day(s), HH:MM:SS" and returns the total number of seconds.

    Args:
        duration_str (str): The duration string to parse, e.g., "806 days, 10:09:07"

    Returns:
        float: Total duration in seconds.

    Raises:
        ValueError: If the input string is not in the expected format.
    """
    # Define a regular expression pattern to capture days, hours, minutes, and seconds
    pattern = r"^(?:(\d+)\s+day[s]?,\s*)?(\d{1,2}):(\d{2}):(\d{2}(?:\.\d+)?)$"
    match = re.match(pattern, duration_str.strip())

    if not match:
        raise ValueError(f"Invalid duration format: '{duration_str}'")

    days, hours, minutes, seconds = match.groups()

    # Convert captured groups to appropriate numerical types, handling optional days
    days = int(days) if days else 0
    hours = int(hours)
    minutes = int(minutes)
    seconds = float(seconds)

    # Create a timedelta object
    td = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)

    # Return total seconds
    return td.total_seconds()


def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Preprocess the DataFrame by parsing dates and durations, and converting durations to desired units.

    Args:
        df (pd.DataFrame): Original DataFrame containing 'start_date', 'end_date', and 'duration' columns.

    Returns:
        pd.DataFrame: Cleaned DataFrame with additional 'duration_seconds' column.
    """
    # Convert 'start_date' and 'end_date' to datetime objects
    df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce")
    df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce")

    # Drop rows with invalid dates
    initial_count = len(df)
    df = df.dropna(subset=["start_date", "end_date"])
    dropped_dates = initial_count - len(df)
    if dropped_dates > 0:
        print(f"Dropped {dropped_dates} rows due to invalid dates.")

    # Parse 'duration' to total seconds
    def safe_parse(duration):
        try:
            return parse_duration(duration)
        except ValueError as e:
            print(e)
            return pd.NA

    df["duration_seconds"] = df["duration"].apply(safe_parse)

    # Drop rows with invalid duration formats
    initial_count = len(df)
    df = df.dropna(subset=["duration_seconds"])
    dropped_durations = initial_count - len(df)
    if dropped_durations > 0:
        print(f"Dropped {dropped_durations} rows due to invalid duration formats.")

    # Ensure that end_date >= start_date
    initial_count = len(df)
    df = df[df["end_date"] >= df["start_date"]]
    dropped_logical = initial_count - len(df)
    if dropped_logical > 0:
        print(
            f"Dropped {dropped_logical} rows where end_date is earlier than start_date."
        )

    return df


def convert_durations(df: pd.DataFrame, unit: str = "days") -> pd.DataFrame:
    """
    Convert the duration from seconds to the specified unit.

    Args:
        df (pd.DataFrame): DataFrame containing 'duration_seconds' column.
        unit (str): The unit to convert durations into ('seconds', 'minutes', 'hours', 'days', 'months', 'years').

    Returns:
        pd.DataFrame: DataFrame with an additional 'duration_converted' column.
    """
    unit_conversions = {
        "seconds": 1,
        "minutes": 60,
        "hours": 3600,
        "days": 86400,
        "months": 86400 * 30.44,  # Average days per month
        "years": 86400 * 365.25,  # Average days per year
    }

    conversion_factor = unit_conversions.get(unit.lower())
    if not conversion_factor:
        raise ValueError(
            f"Invalid unit '{unit}'. Choose from {list(unit_conversions.keys())}."
        )

    df["duration_converted"] = df["duration_seconds"] / conversion_factor

    return df


def calculate_mean_time_to_mitigate(df: pd.DataFrame) -> float:
    """
    Calculate the Mean Time to Mitigate (MTTM) from the provided DataFrame.

    Args:
        df (pd.DataFrame): Preprocessed DataFrame containing 'duration_converted' column.

    Returns:
        float: The MTTM in the specified unit.
    """
    return df["duration_converted"].mean()


def calculate_duration_statistics(df: pd.DataFrame) -> dict:
    """
    Calculate the minimum, maximum, average (mean), and median durations from the provided DataFrame.

    Args:
        df (pd.DataFrame): Preprocessed DataFrame containing 'duration_converted' column.

    Returns:
        dict: A dictionary containing 'min', 'max', 'average', and 'median' durations.
    """
    min_duration = df["duration_converted"].min()
    max_duration = df["duration_converted"].max()
    average_duration = df["duration_converted"].mean()
    median_duration = df["duration_converted"].median()

    statistics = {
        "min": min_duration,
        "max": max_duration,
        "average": average_duration,
        "median": median_duration,
    }

    return statistics


def plot_mttm_histogram(df: pd.DataFrame, unit: str = "days", severity: str = None):
    """
    Plot a histogram of Mitigation Times in the specified unit, optionally filtered by severity.

    Args:
        df (pd.DataFrame): Preprocessed DataFrame containing 'duration_converted' column.
        unit (str): The unit for the histogram ('seconds', 'minutes', 'hours', 'days', 'months', 'years').
        severity (str, optional): The severity level to filter by. If None, plots all severities together.
    """
    plt.figure(figsize=(10, 6))
    if severity:
        subset = df[df["Severity"] == severity]
        plt.hist(
            subset["duration_converted"], bins=30, color="skyblue", edgecolor="black"
        )
        plt.title(
            f"Histogram of Mitigation Times for {severity} Severity ({unit.capitalize()})"
        )
    else:
        plt.hist(df["duration_converted"], bins=30, color="skyblue", edgecolor="black")
        plt.title(f"Histogram of Mitigation Times ({unit.capitalize()})")

    plt.xlabel(f"Duration ({unit})")
    plt.ylabel("Frequency")
    plt.grid(True)
    plt.show()


def plot_severity_statistics_combined(
    df: pd.DataFrame,
    unit: str = "days",
    save_fig: bool = False,
    save_path: str = "severity_statistics_combined.png",
):
    """
    Plot combined severity statistics (Min, Median, Mean, Max) in a single grouped bar chart.

    Args:
        df (pd.DataFrame): Preprocessed DataFrame containing 'Severity' and 'duration_converted' columns.
        unit (str): The unit for the duration ('seconds', 'minutes', 'hours', 'days', 'months', 'years').
        save_fig (bool): Whether to save the figure as an image file.
        save_path (str): The path to save the figure.
    """
    # Set the Seaborn theme for a professional look
    sns.set_theme(style="whitegrid", context="talk", font="serif", palette="colorblind")

    # Calculate statistics: min, median, mean, max for each severity with observed=False
    stats = (
        df.groupby("Severity", observed=False)["duration_converted"]
        .agg(["min", "median", "mean", "max"])
        .reindex(df["Severity"].cat.categories)
    )

    # Check if 'Severity' is in stats
    if "Severity" not in stats.columns and "Severity" not in stats.index.names:
        stats = stats.reset_index()

    # Melt the DataFrame to long-form for Seaborn
    stats_melted = stats.reset_index().melt(
        id_vars="Severity",
        value_vars=["min", "median", "mean", "max"],
        var_name="Statistic",
        value_name="Duration",
    )

    # Define a distinct palette for each statistic
    palette = {"min": "lightgreen", "median": "gold", "mean": "salmon", "max": "plum"}

    # Initialize the matplotlib figure
    plt.figure(figsize=(16, 10))

    # Create a grouped barplot
    ax = sns.barplot(
        data=stats_melted, x="Severity", y="Duration", hue="Statistic", palette=palette
    )

    # Add data labels atop each bar
    for p in ax.patches:
        height = p.get_height()
        if pd.isna(height):
            label = "N/A"
        else:
            label = f"{height:.2f}"
        ax.text(
            p.get_x() + p.get_width() / 2.0,
            height + stats["max"].max() * 0.005,
            label,
            ha="center",
            va="bottom",
            fontsize=12,
            color="black",
        )

    # Set the title and labels with increased font sizes
    plt.title(
        f"Severity Statistics (Min, Median, Mean, Max) in {unit.capitalize()}",
        fontsize=24,
        weight="bold",
    )
    plt.xlabel("Severity", fontsize=18)
    plt.ylabel(f"Duration ({unit})", fontsize=18)

    # Adjust tick parameters for readability
    plt.xticks(rotation=45, fontsize=14)
    plt.yticks(fontsize=14)

    # Customize the legend
    plt.legend(title="Statistic", fontsize=14, title_fontsize=16)

    # Optimize layout
    plt.tight_layout()

    # Save the figure if required
    if save_fig:
        plt.savefig(save_path, dpi=300)

    # Display the plot
    plt.show()

    # Reset Seaborn to default
    sns.reset_orig()


def plot_severity_statistics(
    df: pd.DataFrame,
    unit: str = "days",
    save_fig: bool = False,
    save_path: str = "severity_statistics",
):
    """
    Plot severity statistics information in high-quality graphs suitable for academic research papers.

    This function generates five bar charts:
    1. Number of CVEs per Severity.
    2. Mean Mitigation Time per Severity in the specified unit.
    3. Minimum Mitigation Time per Severity.
    4. Median Mitigation Time per Severity.
    5. Maximum Mitigation Time per Severity.

    Args:
        df (pd.DataFrame): Preprocessed DataFrame containing 'Severity' and 'duration_converted' columns.
        unit (str): The unit for the duration ('seconds', 'minutes', 'hours', 'days', 'months', 'years').
        save_fig (bool): Whether to save the figures as image files.
        save_path (str): The base path to save the figures. Each plot will have a suffix indicating its type.
    """
    # Set the style to 'seaborn-paper' for a clean and professional look
    sns.set_theme(style="whitegrid", context="talk", font="serif", palette="colorblind")

    # Define color palettes for different plots
    palette_counts = sns.color_palette("Blues_d", n_colors=df["Severity"].nunique())
    palette_mean = sns.color_palette("Reds_d", n_colors=df["Severity"].nunique())
    palette_min = sns.color_palette("Greens_d", n_colors=df["Severity"].nunique())
    palette_median = sns.color_palette("Oranges_d", n_colors=df["Severity"].nunique())
    palette_max = sns.color_palette("Purples_d", n_colors=df["Severity"].nunique())

    # 1. Number of CVEs per Severity
    severity_counts = (
        df["Severity"].value_counts(sort=False).reindex(df["Severity"].cat.categories)
    )

    plt.figure(figsize=(12, 8))
    barplot_counts = sns.barplot(
        x=severity_counts.index, y=severity_counts.values, palette=palette_counts
    )

    # Add data labels on top of each bar
    for index, value in enumerate(severity_counts.values):
        plt.text(
            index,
            value + severity_counts.values.max() * 0.01,
            f"{int(value)}",
            ha="center",
            va="bottom",
            fontsize=14,
        )

    plt.title("Number of CVEs per Severity", fontsize=20, weight="bold")
    plt.xlabel("Severity", fontsize=16)
    plt.ylabel("Number of CVEs", fontsize=16)
    plt.xticks(rotation=45, fontsize=14)
    plt.yticks(fontsize=14)
    plt.tight_layout()

    if save_fig:
        plt.savefig(f"{save_path}_count.png", dpi=300)

    plt.show()

    # 2. Mean Mitigation Time per Severity
    severity_mean_duration = (
        df.groupby("Severity")["duration_converted"]
        .mean()
        .reindex(df["Severity"].cat.categories)
    )

    plt.figure(figsize=(12, 8))
    barplot_mean = sns.barplot(
        x=severity_mean_duration.index,
        y=severity_mean_duration.values,
        palette=palette_mean,
    )

    # Add data labels on top of each bar with two decimal points
    for index, value in enumerate(severity_mean_duration.values):
        plt.text(
            index,
            value + severity_mean_duration.values.max() * 0.01,
            f"{value:.2f}",
            ha="center",
            va="bottom",
            fontsize=14,
        )

    plt.title(
        f"Mean Mitigation Time per Severity ({unit.capitalize()})",
        fontsize=20,
        weight="bold",
    )
    plt.xlabel("Severity", fontsize=16)
    plt.ylabel(f"Mean Mitigation Time ({unit})", fontsize=16)
    plt.xticks(rotation=45, fontsize=14)
    plt.yticks(fontsize=14)
    plt.tight_layout()

    if save_fig:
        plt.savefig(f"{save_path}_mean.png", dpi=300)

    plt.show()

    # 3. Minimum Mitigation Time per Severity
    severity_min_duration = (
        df.groupby("Severity")["duration_converted"]
        .min()
        .reindex(df["Severity"].cat.categories)
    )

    plt.figure(figsize=(12, 8))
    barplot_min = sns.barplot(
        x=severity_min_duration.index,
        y=severity_min_duration.values,
        palette=palette_min,
    )

    # Add data labels
    for index, value in enumerate(severity_min_duration.values):
        plt.text(
            index,
            value + severity_min_duration.values.max() * 0.01,
            f"{value:.2f}",
            ha="center",
            va="bottom",
            fontsize=14,
        )

    plt.title(
        f"Minimum Mitigation Time per Severity ({unit.capitalize()})",
        fontsize=20,
        weight="bold",
    )
    plt.xlabel("Severity", fontsize=16)
    plt.ylabel(f"Minimum Mitigation Time ({unit})", fontsize=16)
    plt.xticks(rotation=45, fontsize=14)
    plt.yticks(fontsize=14)
    plt.tight_layout()

    if save_fig:
        plt.savefig(f"{save_path}_min.png", dpi=300)

    plt.show()

    # 4. Median Mitigation Time per Severity
    severity_median_duration = (
        df.groupby("Severity")["duration_converted"]
        .median()
        .reindex(df["Severity"].cat.categories)
    )

    plt.figure(figsize=(12, 8))
    barplot_median = sns.barplot(
        x=severity_median_duration.index,
        y=severity_median_duration.values,
        palette=palette_median,
    )

    # Add data labels
    for index, value in enumerate(severity_median_duration.values):
        plt.text(
            index,
            value + severity_median_duration.values.max() * 0.01,
            f"{value:.2f}",
            ha="center",
            va="bottom",
            fontsize=14,
        )

    plt.title(
        f"Median Mitigation Time per Severity ({unit.capitalize()})",
        fontsize=20,
        weight="bold",
    )
    plt.xlabel("Severity", fontsize=16)
    plt.ylabel(f"Median Mitigation Time ({unit})", fontsize=16)
    plt.xticks(rotation=45, fontsize=14)
    plt.yticks(fontsize=14)
    plt.tight_layout()

    if save_fig:
        plt.savefig(f"{save_path}_median.png", dpi=300)

    plt.show()

    # 5. Maximum Mitigation Time per Severity
    severity_max_duration = (
        df.groupby("Severity")["duration_converted"]
        .max()
        .reindex(df["Severity"].cat.categories)
    )

    plt.figure(figsize=(12, 8))
    barplot_max = sns.barplot(
        x=severity_max_duration.index,
        y=severity_max_duration.values,
        palette=palette_max,
    )

    # Add data labels
    for index, value in enumerate(severity_max_duration.values):
        plt.text(
            index,
            value + severity_max_duration.values.max() * 0.01,
            f"{value:.2f}",
            ha="center",
            va="bottom",
            fontsize=14,
        )

    plt.title(
        f"Maximum Mitigation Time per Severity ({unit.capitalize()})",
        fontsize=20,
        weight="bold",
    )
    plt.xlabel("Severity", fontsize=16)
    plt.ylabel(f"Maximum Mitigation Time ({unit})", fontsize=16)
    plt.xticks(rotation=45, fontsize=14)
    plt.yticks(fontsize=14)
    plt.tight_layout()

    if save_fig:
        plt.savefig(f"{save_path}_max.png", dpi=300)

    plt.show()

    # Reset the theme to default to avoid affecting other plots
    sns.reset_orig()


def calculate_combined_statistics(df, units):
    """
    Calculate and display combined Mean Time to Mitigate (MTTM) and duration statistics
    across all severities for the specified units.
    """
    print("\n--- Combined Mean Time to Mitigate (MTTM) ---")
    for unit in units:
        try:
            df_converted = convert_durations(df.copy(), unit=unit)
            mttm = df_converted["duration_converted"].mean()
            print(f"Mean Time to Mitigate in {unit.capitalize()}: {mttm:.2f} {unit}")
        except ValueError as e:
            print(f"Error calculating MTTM in {unit}: {e}")

    print("\n--- Combined Duration Statistics ---")
    for unit in units:
        try:
            df_converted = convert_durations(df.copy(), unit=unit)
            stats = df_converted["duration_converted"].agg(
                ["min", "max", "mean", "median"]
            )
            print(f"\nDuration Statistics in {unit.capitalize()}:")
            print(f"  Minimum: {stats['min']:.2f} {unit}")
            print(f"  Maximum: {stats['max']:.2f} {unit}")
            print(f"  Average: {stats['mean']:.2f} {unit}")
            print(f"  Median: {stats['median']:.2f} {unit}")
        except ValueError as e:
            print(f"Error calculating statistics in {unit}: {e}")


def main():
    import_path = "data/rq1_cve_lifetimes.csv"
    print(f"Importing data from: {import_path}")
    try:
        df = pd.read_csv(import_path)
    except FileNotFoundError:
        print(f"File not found: {import_path}")
        return
    except pd.errors.EmptyDataError:
        print(f"No data: {import_path} is empty.")
        return
    except pd.errors.ParserError as e:
        print(f"Parsing error: {e}")
        return

    # Ensure the necessary columns exist
    required_columns = {"Start", "End", "Duration", "Severity"}  # Added 'Severity'
    if not required_columns.issubset(df.columns):
        print(df.columns)
        print(f"Missing columns in the CSV. Required columns: {required_columns}")
        return

    # Rename columns for consistency
    df = df[["Start", "End", "Duration", "Severity"]].rename(
        columns={
            "Start": "start_date",
            "End": "end_date",
            "Duration": "duration",
            "Severity": "Severity",
        }
    )

    # Preprocess data
    df = preprocess_data(df)

    if df.empty:
        print("No valid data available after preprocessing.")
        return

    # Handle missing or inconsistent Severity values
    initial_count = len(df)
    df = df.dropna(subset=["Severity"])
    dropped_severity = initial_count - len(df)
    if dropped_severity > 0:
        print(f"Dropped {dropped_severity} rows due to missing Severity values.")

    # Optional: Standardize Severity values (e.g., capitalize)
    df["Severity"] = df["Severity"].str.capitalize()

    # Define the desired order of severities
    severity_order = ["Low", "Moderate", "High", "Critical"]

    # Convert 'Severity' column to categorical with the specified order
    df["Severity"] = pd.Categorical(
        df["Severity"], categories=severity_order, ordered=True
    )

    # Define units for conversion and statistics
    units = ["days", "hours", "minutes", "seconds", "months", "years"]

    # Calculate and display MTTM in various units, grouped by Severity
    print("\n--- Mean Time to Mitigate (MTTM) by Severity ---")
    for unit in units:
        try:
            df_converted = convert_durations(df.copy(), unit=unit)
            mttm_by_severity = df_converted.groupby("Severity")[
                "duration_converted"
            ].mean()
            print(f"\nMean Time to Mitigate in {unit.capitalize()}:")
            for severity, mttm in mttm_by_severity.items():
                print(f"  {severity}: {mttm:.2f} {unit}")
        except ValueError as e:
            print(f"Error calculating MTTM in {unit}: {e}")

    # Calculate and display Duration Statistics in various units, grouped by Severity
    print("\n--- Duration Statistics by Severity ---")
    for unit in units:
        try:
            df_converted = convert_durations(df.copy(), unit=unit)
            stats_by_severity = df_converted.groupby("Severity")[
                "duration_converted"
            ].agg(["min", "max", "mean", "median"])
            print(f"\nDuration Statistics in {unit.capitalize()}:")
            for severity, stats in stats_by_severity.iterrows():
                print(f"  {severity}:")
                print(f"    Minimum: {stats['min']:.2f} {unit}")
                print(f"    Maximum: {stats['max']:.2f} {unit}")
                print(f"    Average: {stats['mean']:.2f} {unit}")
                print(f"    Median: {stats['median']:.2f} {unit}")
        except ValueError as e:
            print(f"Error calculating statistics in {unit}: {e}")

    # Calculate and display Combined Statistics across all Severities
    calculate_combined_statistics(df, units)

    # Plot Severity Statistics
    print("\n--- Plotting Severity Statistics ---")
    unit_to_plot = "days"  # Choose the unit you want to visualize
    try:
        df_converted = convert_durations(df.copy(), unit=unit_to_plot)
        plot_severity_statistics(df_converted, unit=unit_to_plot)
        plot_severity_statistics_combined(df=df_converted, unit=unit_to_plot)
    except Exception as e:
        print(f"Error plotting severity statistics: {e}")

    # Optional: Plot histogram for each Severity in a specific unit
    # Uncomment the lines below to enable plotting for each severity
    """
    print("\n--- Plotting Histogram by Severity ---")
    unit_to_plot = 'days'  # Change as needed
    for severity in df["Severity"].unique():
        try:
            df_converted = convert_durations(df.copy(), unit=unit_to_plot)
            plot_mttm_histogram(df_converted, unit=unit_to_plot, severity=severity)
        except Exception as e:
            print(f"Error plotting histogram for {severity} severity: {e}")
    """

    # Optional: Plot combined histogram with different colors for each Severity
    # Uncomment the lines below to enable combined plotting
    print("\n--- Plotting Combined Histogram by Severity ---")
    unit_to_plot = "days"  # Change as needed
    try:
        df_converted = convert_durations(df.copy(), unit=unit_to_plot)
        plt.figure(figsize=(10, 6))
        for severity in df_converted["Severity"].unique():
            subset = df_converted[df_converted["Severity"] == severity]
            plt.hist(subset["duration_converted"], bins=50, alpha=0.5, label=severity)
        plt.title(
            f"Histogram of Mitigation Times by Severity ({unit_to_plot.capitalize()})"
        )
        plt.xlabel(f"Duration ({unit_to_plot})")
        plt.ylabel("Frequency")
        plt.legend(title="Severity")
        plt.grid(True)
        plt.show()
    except Exception as e:
        print(f"Error plotting combined histogram: {e}")


if __name__ == "__main__":
    main()
