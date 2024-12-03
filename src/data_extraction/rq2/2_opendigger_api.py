import requests
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import csv
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from ...utils.config import RQ2_OPENDIGGER_INPUT, MAX_WORKERS

# Define the base URL and default parameters
base_url = "https://oss.x-lab.info/open_digger/github/"
type_ = "participants"


# Function to fetch JSON data from the API
def fetch_data(base_url, repo_name, type_):
    api_url = f"{base_url}{repo_name}/{type_}.json"
    api_url = api_url.replace(" ", "%20")
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        print(f"Data successfully fetched from {api_url}")
        return data
    except requests.exceptions.RequestException as e:
        print(f"Failed to retrieve data for {repo_name}: {e}")
        return None


# Function to process data and compute accumulated values
def process_data(data):
    # Filter keys where key length is 7 (e.g., '2020-01')
    keys = [k for k in data.keys() if len(k) == 7]
    # Sort the keys chronologically
    keys.sort()
    # Extract values corresponding to the filtered keys
    values = [data[k] for k in keys]
    # Compute accumulated values
    acc_values = []
    total = 0
    for v in values:
        total += v
        acc_values.append(total)
    return keys, values, acc_values


def save_to_csv(keys, values, acc_values, repo_name, type_):
    # Sanitize repo_name to make it a valid folder name
    folder_name = repo_name.replace("/", "_")
    folder_path = f"data/rq2_opendigger/{folder_name}"

    # Create the folder if it doesn't exist
    os.makedirs(folder_path, exist_ok=True)

    # Set the filename to be 'type_.csv'
    filename = f"{folder_path}/{type_}.csv"

    try:
        with open(filename, "w", newline="") as csvfile:
            fieldnames = ["Date", "Monthly Value", "Accumulated Value"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for i in range(len(keys)):
                writer.writerow(
                    {
                        "Date": keys[i],
                        "Monthly Value": values[i],
                        "Accumulated Value": acc_values[i],
                    }
                )
        print(f"Data saved to {filename}")
    except Exception as e:
        print(f"Failed to save data for {repo_name}: {e}")


def process_repository(repo_info):
    idx, total_rows, github_owner, github_repo = repo_info
    repo_name = f"{github_owner}/{github_repo}"
    print(f"\nProcessing {idx + 1}/{total_rows}: {repo_name}")

    # Fetch data from the API
    data = fetch_data(base_url, repo_name, type_)
    if data:
        # Process the data
        keys, values, acc_values = process_data(data)
        # Save the data to a CSV file
        save_to_csv(keys, values, acc_values, repo_name, type_)
        return True
    else:
        print(f"Skipping {repo_name} due to data retrieval failure.")
        return False


# Main execution
if __name__ == "__main__":
    file_path = RQ2_OPENDIGGER_INPUT
    try:
        with open(file_path, "r") as csvfile:
            reader = csv.DictReader(csvfile)
            # Read all rows into a list to get the total count
            rows = list(reader)
            total_rows = len(rows)
            print(f"Total repositories to process: {total_rows}")

            start_time = time.time()

            # Create list of repository info tuples
            repo_infos = [
                (idx, total_rows, row["github_owner"], row["github_repo"])
                for idx, row in enumerate(rows)
            ]

            # Process repositories using thread pool
            completed = 0
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                future_to_repo = {
                    executor.submit(process_repository, repo_info): repo_info
                    for repo_info in repo_infos
                }

                for future in as_completed(future_to_repo):
                    completed += 1
                    # Calculate progress and timing info
                    elapsed_time = time.time() - start_time
                    avg_time_per_repo = elapsed_time / completed
                    remaining_repos = total_rows - completed
                    eta = avg_time_per_repo * remaining_repos
                    print(f"Completed: {completed}/{total_rows}")
                    print(f"Elapsed time: {elapsed_time:.2f}s, ETA: {eta:.2f}s")

    except Exception as e:
        print(f"Failed to read repo information from {file_path}: {e}")
