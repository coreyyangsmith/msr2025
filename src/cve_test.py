import requests
import csv
import sys


def retrieve_data(url, query_payload):
    """
    Sends a POST request to the specified URL with the given query payload.

    Args:
        url (str): The endpoint URL.
        query_payload (dict): The JSON payload for the POST request.

    Returns:
        list: List of release dictionaries retrieved from the response.

    Raises:
        requests.exceptions.RequestException: If the request fails.
        ValueError: If the response JSON is not in the expected format.
    """
    try:
        response = requests.post(url, json=query_payload)
        response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        print(f"Error during POST request: {e}")
        sys.exit(1)

    try:
        data = response.json()
    except ValueError:
        print("Response content is not valid JSON.")
        sys.exit(1)

    # Assuming the JSON structure contains a key that holds the list of releases.
    # Adjust the following line based on the actual structure of your response.
    # For example, if the releases are under 'data', use data['data']
    # Here, we'll assume the response is a list of release dictionaries.
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        return data
    else:
        print("Unexpected JSON structure.")
        sys.exit(1)


def filter_data(data):
    """
    Filters items where the 'cve' list has a length greater than 0.

    Args:
        data (list): List of dictionaries.

    Returns:
        list: Filtered list of dictionaries.
    """
    filtered = [
        item
        for item in data
        if "cve" in item and isinstance(item["cve"], list) and len(item["cve"]) > 0
    ]
    return filtered


def main():
    # Define the URL and endpoint
    url = "http://localhost:8080/cypher"

    # Define the output CSV file path
    output_csv = "filtered_data.csv"  # You can change this as needed

    # Initialize batch parameters
    batch_size = 1000
    offset = 0
    total_items_retrieved = 0
    total_items_filtered = 0

    # Flag to check if headers are written
    headers_written = False

    # Keep looping until there's no more data
    while True:
        # Define the query with SKIP and LIMIT
        retrieve_data_query = {
            "query": f"MATCH (r:Release) RETURN r SKIP {offset} LIMIT {batch_size}",
            "addedValues": ["CVE"],
        }

        # Step 1: Retrieve Data
        print(f"Retrieving data from the server... (offset: {offset})")
        data = retrieve_data(url, retrieve_data_query)

        if not data:
            print("No more data to retrieve.")
            break

        print(f"Total items retrieved in this batch: {len(data)}")
        total_items_retrieved += len(data)

        # Step 2: Filter Data
        print("Filtering data with non-empty 'cve' lists...")
        filtered = filter_data(data)
        print(f"Total items after filtering in this batch: {len(filtered)}")
        total_items_filtered += len(filtered)

        # Step 3: Write to CSV
        if filtered:
            # Write to CSV
            print(f"Writing filtered data to '{output_csv}'...")
            # If headers are not written yet, write them
            if not headers_written:
                headers = filtered[0].keys()
                try:
                    with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
                        writer = csv.DictWriter(csvfile, fieldnames=headers)
                        writer.writeheader()
                except IOError as e:
                    print(f"IO error while writing to CSV: {e}")
                    sys.exit(1)
                headers_written = True

            # Now append data to CSV
            try:
                with open(output_csv, "a", newline="", encoding="utf-8") as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=headers)
                    for item in filtered:
                        # If 'cve' is a list, join it into a comma-separated string
                        if isinstance(item.get("cve"), list):
                            item["cve"] = ", ".join(map(str, item["cve"]))
                        writer.writerow(item)
            except IOError as e:
                print(f"IO error while writing to CSV: {e}")
                sys.exit(1)
        else:
            print("No items with non-empty 'cve' lists found in this batch.")

        # Increment offset
        offset += batch_size

    print(f"Total items retrieved: {total_items_retrieved}")
    print(f"Total items after filtering: {total_items_filtered}")
    print("Processing completed.")


if __name__ == "__main__":
    main()
