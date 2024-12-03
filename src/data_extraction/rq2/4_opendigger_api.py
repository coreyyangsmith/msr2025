import requests
import csv
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from ...utils.config import RQ2_4_INPUT, OPENDIGGER_VALUES, MAX_WORKERS

# Define the base URL and max workers
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


def process_repo(repo_name):
    """Process a single repository for all metric types."""
    for type_ in OPENDIGGER_VALUES:
        print(f"Processing {repo_name} - {type_}")
        data = fetch_data(BASE_URL, repo_name, type_)
        if data:
            keys, values, acc_values = process_data(data)
            save_to_csv(keys, values, acc_values, repo_name, type_)
        else:
            print(f"Skipping {repo_name} type {type_} due to data retrieval failure.")
    return repo_name


def main():
    try:
        with open(RQ2_4_INPUT, "r") as f:
            repos = [line.strip() for line in f if line.strip()]
            total_repos = len(repos)
            print(f"Total repositories to process: {total_repos}")

            start_time = time.time()
            completed = 0

            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                # Submit all tasks
                future_to_repo = {
                    executor.submit(process_repo, repo): repo for repo in repos
                }

                # Process completed tasks
                for future in as_completed(future_to_repo):
                    repo = future_to_repo[future]
                    try:
                        future.result()
                        completed += 1

                        # Calculate progress and timing
                        elapsed_time = time.time() - start_time
                        avg_time_per_repo = elapsed_time / completed
                        remaining_repos = total_repos - completed
                        eta = avg_time_per_repo * remaining_repos

                        print(f"\nProgress: {completed}/{total_repos}")
                        print(
                            f"Elapsed time: {format_time(elapsed_time)}, ETA: {format_time(eta)}"
                        )

                    except Exception as e:
                        print(f"Error processing {repo}: {e}")

    except Exception as e:
        print(f"Failed to read repo information from {RQ2_4_INPUT}: {e}")


if __name__ == "__main__":
    main()
