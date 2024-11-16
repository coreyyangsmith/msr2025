import requests
import csv
import time
import os
from ...utils.config import (
    RQ2_13_INPUT,
    OPENDIGGER_VALUES,
    RQ2_13_OPENDIGGER_OUTPUT,
    MAX_WORKERS,
)
import concurrent.futures

# Define the base URL
BASE_URL = "https://oss.x-lab.info/open_digger/github/"


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
    folder_path = os.path.join("data", RQ2_13_OPENDIGGER_OUTPUT, folder_name)

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


# Function to process a single (repo_name, type_) pair
def process_repo_type(repo_name, type_):
    print(f"Processing {repo_name} - {type_}")
    # Fetch data from the API
    data = fetch_data(BASE_URL, repo_name, type_)
    if data:
        # Process the data
        keys, values, acc_values = process_data(data)
        # Save the data to a CSV file
        save_to_csv(keys, values, acc_values, repo_name, type_)
    else:
        print(f"Skipping {repo_name} type {type_} due to data retrieval failure.")


def main():
    # Replace this with the actual path to your input file
    file_path = RQ2_13_INPUT

    try:
        with open(file_path, "r") as f:
            # Read all lines, strip whitespace and newlines
            rows = [line.strip() for line in f if line.strip()]
            total_tasks = len(rows) * len(OPENDIGGER_VALUES)
            print(f"Total tasks to process: {total_tasks}")

        start_time = time.time()
        completed_tasks = 0

        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_repo_type = {}
            for repo_name in rows:
                for type_ in OPENDIGGER_VALUES:
                    future = executor.submit(process_repo_type, repo_name, type_)
                    future_to_repo_type[future] = (repo_name, type_)

            for future in concurrent.futures.as_completed(future_to_repo_type):
                repo_name, type_ = future_to_repo_type[future]
                try:
                    future.result()
                    print(f"Completed processing {repo_name} - {type_}")
                except Exception as exc:
                    print(f"Error processing {repo_name} - {type_}: {exc}")

                completed_tasks += 1

                # Calculate elapsed time and ETA
                elapsed_time = time.time() - start_time
                avg_time_per_task = elapsed_time / completed_tasks
                remaining_tasks = total_tasks - completed_tasks
                eta = avg_time_per_task * remaining_tasks
                print(
                    f"Elapsed time: {format_time(elapsed_time)}, ETA: {format_time(eta)}"
                )

    except Exception as e:
        print(f"Failed to read repo information from {file_path}: {e}")


if __name__ == "__main__":
    main()
