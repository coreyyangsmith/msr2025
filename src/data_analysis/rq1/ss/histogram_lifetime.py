import re

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from datetime import timedelta
# https://chatgpt.com/share/66fde09b-06b4-8012-9854-ca77ce8eb344


def plot_duration_histogram_over_time(df: pd.DataFrame):
    """
    Plots a histogram distribution over time for durations.

    Parameters:
    - data: list of tuples or lists, where each element is (start_date_str, end_date_str, duration_str)
    """
    # Create DataFrame from data
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
    df["duration_days"] = df["duration_seconds"] / 86400

    # Convert dates to numerical format for plotting
    x = mdates.date2num(df["start_date"])
    y = df["duration_days"]

    # Create 2D histogram
    plt.figure(figsize=(12, 6))
    plt.hist2d(x, y, bins=[50, 50], cmap="Blues")
    plt.colorbar(label="Counts")

    # Format plot
    plt.xlabel("Start Date")
    plt.ylabel("Duration (days)")
    plt.title("Histogram Distribution of Durations Over Time")
    plt.gca().xaxis_date()
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


# Example usage with sample data
data = [
    ("2005-08-01 03:52:02", "2013-02-20 13:20:05", "2760 days, 9:28:03"),
]


import_path = "data/rq1_cve_lifetimes.csv"
print(import_path)
df = pd.read_csv(import_path)
df = df[["Start", "End", "Duration"]]
df = df.rename(
    columns={"Start": "start_date", "End": "end_date", "Duration": "duration"}
)
plot_duration_histogram_over_time(df)
