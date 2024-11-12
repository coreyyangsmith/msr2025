import requests
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import csv
import time
import os  # Import os module to handle file paths and directories

from ...utils.config import RQ2_OPENDIGGER_INPUT

# Define the base URL and default parameters
base_url = "https://oss.x-lab.info/open_digger/github/"
# type_ = "attention"  # Default type
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


# Function to plot the chart
def plot_chart(keys, values, acc_values, repo_name, type_):
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Plot bar chart on ax1
    ax1.bar(keys, values, color="skyblue", label="Monthly Value")
    ax1.set_xlabel("Date")
    ax1.set_ylabel("Monthly Value", color="blue")
    ax1.tick_params(axis="y", labelcolor="blue")

    # Create a second y-axis for the accumulated values
    ax2 = ax1.twinx()
    ax2.plot(keys, acc_values, color="red", label="Accumulated Value", linewidth=2)
    ax2.set_ylabel("Accumulated Value", color="red")
    ax2.tick_params(axis="y", labelcolor="red")

    # Improve the x-axis date formatting
    ax1.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    plt.xticks(rotation=45)

    # Add title and legends
    plt.title(f"Index/Metric {type_} for {repo_name}")
    fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.9))

    plt.tight_layout()
    plt.show()


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
            for idx, row in enumerate(rows):
                github_owner = row["github_owner"]
                github_repo = row["github_repo"]
                repo_name = f"{github_owner}/{github_repo}"
                print(f"\nProcessing {idx + 1}/{total_rows}: {repo_name}")
                # Fetch data from the API
                data = fetch_data(base_url, repo_name, type_)
                if data:
                    # Process the data
                    keys, values, acc_values = process_data(data)
                    # Save the data to a CSV file
                    save_to_csv(keys, values, acc_values, repo_name, type_)
                else:
                    print(f"Skipping {repo_name} due to data retrieval failure.")
                # Calculate elapsed time and estimated time remaining
                elapsed_time = time.time() - start_time
                avg_time_per_repo = elapsed_time / (idx + 1)
                remaining_repos = total_rows - (idx + 1)
                eta = avg_time_per_repo * remaining_repos
                print(f"Elapsed time: {elapsed_time:.2f}s, " f"ETA: {eta:.2f}s")
    except Exception as e:
        print(f"Failed to read repo information from {file_path}: {e}")