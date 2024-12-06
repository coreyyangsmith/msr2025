import pandas as pd
from datetime import timedelta
import re

from ...utils import MTTM_UNIT, RQ1_MTTM_INPUT


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
    pattern = r"^(?:(\d+)\s+day[s]?,\s*)?(\d{1,2}):(\d{2}):(\d{2}(?:\.\d+)?)$"
    match = re.match(pattern, duration_str.strip())

    if not match:
        raise ValueError(f"Invalid duration format: '{duration_str}'")

    days, hours, minutes, seconds = match.groups()

    days = int(days) if days else 0
    hours = int(hours)
    minutes = int(minutes)
    seconds = float(seconds)

    td = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
    return td.total_seconds()


def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Preprocess the DataFrame by parsing dates and calculating MTTM.

    Args:
        df (pd.DataFrame): Original DataFrame containing 'patched_version_date', 'cve_publish_date' columns.

    Returns:
        pd.DataFrame: Cleaned DataFrame with additional 'duration_seconds' column.
    """
    # Convert dates to datetime objects with UTC timezone
    df["patched_date"] = pd.to_datetime(
        df["patched_version_date"], errors="coerce", utc=True
    )
    df["publish_date"] = pd.to_datetime(
        df["cve_publish_date"], errors="coerce", utc=True
    )

    # Drop rows with invalid dates
    initial_count = len(df)
    df = df.dropna(subset=["patched_date", "publish_date"])
    dropped_dates = initial_count - len(df)
    if dropped_dates > 0:
        print(f"Dropped {dropped_dates} rows due to invalid dates.")

    # Calculate duration in seconds between patched date and publish date
    df["duration_seconds"] = (
        df["patched_date"] - df["publish_date"]
    ).dt.total_seconds()

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


def generate_mttm_table(df: pd.DataFrame, unit: str = "days") -> pd.DataFrame:
    """
    Generate a table with Mean Time to Mitigate (MTTM) categorized by severity and dataclass.

    Args:
        df (pd.DataFrame): Preprocessed DataFrame containing 'severity', 'dataclass', and 'duration_converted' columns.
        unit (str): The unit for MTTM ('seconds', 'minutes', 'hours', 'days', 'months', 'years').

    Returns:
        pd.DataFrame: A table with 'dataclass', 'severity', 'mean_mttm', and 'count'.
    """
    # Group by 'dataclass' and 'severity'
    grouped = (
        df.groupby(["data_class", "severity"])
        .agg(
            mean_mttm=("duration_converted", "mean"),
            count=("duration_converted", "count"),
        )
        .reset_index()
    )

    # Optionally, format the mean_mttm to two decimal places
    grouped["mean_mttm"] = grouped["mean_mttm"].round(2)

    # Rename columns for clarity
    grouped = grouped.rename(
        columns={"mean_mttm": f"Mean_MTTM ({unit.capitalize()})", "count": "Count"}
    )

    # Calculate total count for each data class
    class_totals = df.groupby("data_class")["duration_converted"].count().reset_index()
    class_totals = class_totals.rename(columns={"duration_converted": "Total Count"})

    return grouped, class_totals


def main():
    import_path = "data/rq0_4_unique_cves_filtered.csv"
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

    # Filter out data_class 2 and invalid data
    df = df[df["data_class"].isin([0, 1])]

    # Print rows with invalid data
    invalid_data = df[df["data_class"] == -1]
    if not invalid_data.empty:
        print("\n--- Rows with Invalid Data ---")
        print(invalid_data.to_string())
        print(f"\nTotal invalid rows: {len(invalid_data)}")

    # Ensure the necessary columns exist
    required_columns = {
        "patched_version_date",
        "cve_publish_date",
        "severity",
        "data_class",
    }
    if not required_columns.issubset(df.columns):
        print(f"Missing columns in the CSV. Required columns: {required_columns}")
        missing = required_columns - set(df.columns)
        print(f"Missing columns: {missing}")
        return

    # Preprocess data
    df = preprocess_data(df)

    if df.empty:
        print("No valid data available after preprocessing.")
        return

    # Handle missing or inconsistent Severity values
    initial_count = len(df)
    df = df.dropna(subset=["severity"])
    dropped_severity = initial_count - len(df)
    if dropped_severity > 0:
        print(f"Dropped {dropped_severity} rows due to missing Severity values.")

    # Optional: Standardize Severity values (e.g., capitalize)
    df["severity"] = df["severity"].str.capitalize()

    # Define the desired order of severities if categorical
    severity_order = ["Low", "Moderate", "High", "Critical"]

    # Convert 'severity' column to categorical with the specified order
    df["severity"] = pd.Categorical(
        df["severity"], categories=severity_order, ordered=True
    )

    # Check if 'dataclass' exists and handle it
    if "data_class" not in df.columns:
        print("The 'dataclass' column is missing from the data.")
        return

    # Define units for conversion
    unit = (
        MTTM_UNIT if "MTTM_UNIT" in globals() else "days"
    )  # Default to 'days' if not defined

    # Convert durations to the specified unit
    try:
        df_converted = convert_durations(df.copy(), unit=unit)
    except ValueError as e:
        print(f"Error converting durations: {e}")
        return

    # Generate the MTTM table and class totals
    mttm_table, class_totals = generate_mttm_table(df_converted, unit=unit)

    # Display the tables
    print("\n--- Mean Time to Mitigate (MTTM) by Dataclass and Severity ---")
    print(mttm_table.to_string(index=False))

    print("\n--- Total Count by Dataclass ---")
    print(class_totals.to_string(index=False))

    # Optionally, save the tables to CSV files
    try:
        mttm_table.to_csv("mttm_summary_table.csv", index=False)
        class_totals.to_csv("class_totals.csv", index=False)
        print("\nSummary tables saved to mttm_summary_table.csv and class_totals.csv")
    except Exception as e:
        print(f"Error saving the summary tables: {e}")


if __name__ == "__main__":
    main()
