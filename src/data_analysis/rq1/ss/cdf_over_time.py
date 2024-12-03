import pandas as pd
import matplotlib.pyplot as plt
import re
from datetime import timedelta
import numpy as np


def plot_duration_cdf(df: pd.DataFrame):
    """
    Plots the Cumulative Distribution Function (CDF) of durations.

    Parameters:
    - df: pd.DataFrame with columns 'start_date', 'end_date', and 'duration'
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

    # Sort the durations for CDF
    sorted_durations = np.sort(df["duration_days"])
    # Calculate the cumulative probabilities
    cdf = np.arange(1, len(sorted_durations) + 1) / len(sorted_durations)

    # Plot the CDF
    plt.figure(figsize=(10, 6))
    plt.plot(sorted_durations, cdf, color="green", linestyle="-", linewidth=2)
    plt.xlabel("Duration (days)")
    plt.ylabel("Cumulative Probability")
    plt.title("Cumulative Distribution Function (CDF) of Durations")
    plt.grid(True)
    plt.tight_layout()
    plt.show()


# Example usage with sample data
if __name__ == "__main__":
    import_path = "data/rq1_cve_lifetimes.csv"
    print(import_path)
    df = pd.read_csv(import_path)
    df = df[["Start", "End", "Duration"]]
    df = df.rename(
        columns={"Start": "start_date", "End": "end_date", "Duration": "duration"}
    )

    # Use the sample DataFrame for plotting
    plot_duration_cdf(df)
