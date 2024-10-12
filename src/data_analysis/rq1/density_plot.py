import re
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns  # Ensure Seaborn is imported
import numpy as np
from datetime import timedelta


def plot_duration_density_over_time_seaborn(df: pd.DataFrame):
    """
    Plots a density distribution over time for durations using Seaborn.

    Parameters:
    - df: pandas DataFrame with 'start_date', 'end_date', and 'duration' columns
    """
    # Parse dates
    df["start_date"] = pd.to_datetime(df["start_date"])
    df["end_date"] = pd.to_datetime(df["end_date"])

    # Function to parse duration string
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

    # Parse duration
    df["duration_seconds"] = df["duration"].apply(parse_duration)
    df["duration_days"] = df["duration_seconds"] / 86400  # Convert seconds to days

    # Plot using Seaborn's kdeplot
    plt.figure(figsize=(12, 6))
    contour = sns.kdeplot(
        data=df,
        x="start_date",
        y="duration_days",
        cmap="Blues",
        fill=True,
        thresh=0,
        levels=100,
    )

    # Add colorbar using one of the contour collections
    plt.colorbar(contour.collections[0], label="Density")

    # Format plot
    plt.xlabel("Start Date")
    plt.ylabel("Duration (days)")
    plt.title("Density Distribution of Durations Over Time")
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


# Example usage with your CSV data
import_path = "data/cve_lifetimes.csv"
print(f"Importing data from: {import_path}")
df = pd.read_csv(import_path)
df = df[["Start", "End", "Duration"]]
df = df.rename(
    columns={"Start": "start_date", "End": "end_date", "Duration": "duration"}
)
plot_duration_density_over_time_seaborn(df)
