import requests
import csv
import time
import os
from ...utils.config import RQ2_4_INPUT

# Define the base URL
BASE_URL = "https://oss.x-lab.info/open_digger/github/"

# Define the list of type_ values to iterate through
VALUES = [
    "issues_new",
    "issues_closed",
    "issue_comments",
    "issue_response_time",
    "issue_resolution_duration",
    "issue_age",
    "code_change_lines_add",
    "code_change_lines_remove",
    "code_change_lines_sum",
    "change_requests",
    "change_requests_accepted",
    "change_requests_reviews",
    "change_request_response_time",
    "change_request_resolution_duration",
    "change_request_age",
    "bus_factor",
    "inactive_contributors",
    "activity",
    "new_contributors",
    "attention",
    "stars",
    "technical_fork",
    "participants",
    "openrank",
]


# Function to fetch JSON data from the API
def fetch_data(base_url, repo_name, type_):
    api_url = f"{base_url}{repo_name}/{type_}.json".replace(" ", "%20")
    print(f"Fetching data from: {api_url}")
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        print(f"Data successfully fetched for {repo_name} - {type_}")
        return data
    except requests.exceptions.RequestException as e:
        print(f"Failed to retrieve data for {repo_name} and type {type_}: {e}")
        return None


# Function to process data and compute accumulated values
def process_data(data):
    # Filter keys where key length is 7 (e.g., '2020-01')
    keys = sorted([k for k in data.keys() if len(k) == 7])
    # Extract values corresponding to the filtered keys
    values = [data[k] for k in keys]
    # Compute accumulated values
    acc_values = []
    total = 0
    for v in values:
        total += v
        acc_values.append(total)
    return keys, values, acc_values


# Function to save data to a CSV file
def save_to_csv(keys, values, acc_values, repo_name, type_):
    # Sanitize repo name to make it a valid folder name
    folder_name = repo_name.replace("/", "_")
    folder_path = os.path.join("data", "rq2_opendigger", folder_name)

    # Create the folder if it doesn't exist
    os.makedirs(folder_path, exist_ok=True)

    # Set the filename to be 'type_.csv'
    filename = os.path.join(folder_path, f"{type_}.csv")

    try:
        with open(filename, "w", newline="") as csvfile:
            fieldnames = ["Date", "Monthly Value", "Accumulated Value"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for date, value, acc_value in zip(keys, values, acc_values):
                writer.writerow(
                    {
                        "Date": date,
                        "Monthly Value": value,
                        "Accumulated Value": acc_value,
                    }
                )
        print(f"Data saved to {filename}")
    except Exception as e:
        print(f"Failed to save data for {repo_name} and type {type_}: {e}")


def format_time(seconds):
    """Format time in seconds to hh:mm:ss string."""
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}h:{minutes}m:{seconds}s"


def main():
    # Replace this with the actual path to your input file
    file_path = RQ2_4_INPUT

    try:
        with open(file_path, "r") as f:
            # Read all lines, strip whitespace and newlines
            rows = [line.strip() for line in f if line.strip()]
            total_rows = len(rows)
            print(f"Total repositories to process: {total_rows}")
            start_time = time.time()
            for idx, repo_name in enumerate(rows):
                print(f"\nProcessing {idx + 1}/{total_rows}: {repo_name}")
                for type_ in VALUES:
                    print(f"  Processing type: {type_}")
                    # Fetch data from the API
                    data = fetch_data(BASE_URL, repo_name, type_)
                    if data:
                        # Process the data
                        keys, values, acc_values = process_data(data)
                        # Save the data to a CSV file
                        save_to_csv(keys, values, acc_values, repo_name, type_)
                    else:
                        print(
                            f"  Skipping {repo_name} type {type_} due to data retrieval failure."
                        )
                # Calculate elapsed time and estimated time remaining
                elapsed_time = time.time() - start_time
                avg_time_per_repo = elapsed_time / (idx + 1)
                remaining_repos = total_rows - (idx + 1)
                eta = avg_time_per_repo * remaining_repos
                print(
                    f"Elapsed time: {format_time(elapsed_time)}, ETA: {format_time(eta)}"
                )
    except Exception as e:
        print(f"Failed to read repo information from {file_path}: {e}")


if __name__ == "__main__":
    main()
