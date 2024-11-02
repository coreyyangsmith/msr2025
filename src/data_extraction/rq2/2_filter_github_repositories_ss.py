import json
import csv
import re
import sys
from typing import List, Dict, Any, Union
from urllib.parse import urlparse

"""
Just filters the URL references provided from OSV.DEV
"""


def load_json(file_path: str) -> List[Dict[str, Any]]:
    """
    Loads JSON data from a file.

    :param file_path: Path to the JSON file.
    :return: List of JSON objects.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("JSON data is not a list of items.")
            return data
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode JSON - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


def load_csv(file_path: str, api_refs_delimiter: str = ";") -> List[Dict[str, Any]]:
    """
    Loads CSV data from a file.

    :param file_path: Path to the CSV file.
    :param api_refs_delimiter: Delimiter used to separate API references in the CSV field.
    :return: List of CSV rows as dictionaries.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            data = []
            for row in reader:
                # Parse "API_References" from a delimited string to a list
                api_refs = row.get("API_References", "")
                if api_refs:
                    row["API_References"] = [
                        ref.strip() for ref in api_refs.split(api_refs_delimiter)
                    ]
                else:
                    row["API_References"] = []
                data.append(row)
            return data
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
    except csv.Error as e:
        print(f"Error: Failed to read CSV - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


def extract_github_url(api_refs: List[str]) -> Union[str, None]:
    """
    Extracts the first GitHub URL from a list of API references.

    :param api_refs: List of API reference strings.
    :return: The first GitHub URL found, or None if none exists.
    """
    # Regex pattern to match GitHub URLs
    github_pattern = re.compile(
        r'https?://[^ \t\n\r\f\v"]*github[^ \t\n\r\f\v"]*', re.IGNORECASE
    )

    for ref in api_refs:
        # Split the reference string into individual URLs
        urls = re.findall(r'https?://[^\s,;"\'<>]+', ref)
        for url in urls:
            if github_pattern.search(url):
                return url  # Return the first GitHub URL found
    return None


def filter_items(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filters items that have at least one GitHub URL in their "API_References"
    and adds a new field "GitHub_URL" containing the extracted URL.

    :param data: List of JSON or CSV objects.
    :return: Filtered list of objects with "GitHub_URL" field added.
    """
    filtered = []
    for item in data:
        api_refs = item.get("API_References", [])
        if not isinstance(api_refs, list):
            print(
                f"Warning: 'API_References' is not a list in item {item}. Skipping this item."
            )
            continue
        github_url = extract_github_url(api_refs)
        if github_url:
            # Add the GitHub URL to the item
            item["GitHub_URL"] = github_url
            filtered.append(item)
    return filtered


def save_json(data: List[Dict[str, Any]], file_path: str):
    """
    Saves JSON data to a file.

    :param data: List of JSON objects to save.
    :param file_path: Path to the output JSON file.
    """
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print(f"Filtered data has been saved to '{file_path}'.")
    except Exception as e:
        print(f"Error: Failed to save JSON - {e}")
        sys.exit(1)


def save_csv(
    data: List[Dict[str, Any]],
    file_path: str,
    api_refs_delimiter: str = ";",
    github_delimiter: str = ", ",
):
    """
    Saves CSV data to a file.

    :param data: List of CSV rows as dictionaries.
    :param file_path: Path to the output CSV file.
    :param api_refs_delimiter: Delimiter to join API references in the CSV field.
    :param github_delimiter: Delimiter to join GitHub URLs in the CSV field.
    """
    if not data:
        print("Warning: No data to save.")
        return

    # Get all field names from the first item, including 'GitHub_URL'
    fieldnames = list(data[0].keys())

    try:
        with open(file_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                # Join "API_References" list into a delimited string
                api_refs = row.get("API_References", [])
                if isinstance(api_refs, list):
                    row["API_References"] = api_refs_delimiter.join(api_refs)
                else:
                    row["API_References"] = ""

                # Handle "GitHub_URL"
                github_url = row.get("GitHub_URL", "")
                if isinstance(github_url, list):
                    row["GitHub_URL"] = github_delimiter.join(github_url)
                elif isinstance(github_url, str):
                    row["GitHub_URL"] = github_url
                else:
                    row["GitHub_URL"] = ""

                writer.writerow(row)
        print(f"Filtered data has been saved to '{file_path}'.")
    except Exception as e:
        print(f"Error: Failed to save CSV - {e}")
        sys.exit(1)


def main():
    """
    Main function to execute the script.
    Usage: python filter_github_references.py <input_file> <output_file>
    Supports JSON and CSV formats based on the file extension.
    """

    # For flexibility, accept input and output file paths as command-line arguments

    input_file = "data/cve_lifetimes_updated.csv"
    output_file = "data/cve_lifetimes_gh_filtered.csv"

    # Determine the file format based on the file extension
    input_ext = input_file.split(".")[-1].lower()
    output_ext = output_file.split(".")[-1].lower()

    if input_ext not in ["json", "csv"]:
        print("Error: Input file must be a JSON or CSV file.")
        sys.exit(1)

    if output_ext not in ["json", "csv"]:
        print("Error: Output file must be a JSON or CSV file.")
        sys.exit(1)

    # Load data
    print(f"Loading data from '{input_file}'...")
    if input_ext == "json":
        data = load_json(input_file)
    elif input_ext == "csv":
        data = load_csv(input_file)
    else:
        print("Error: Unsupported input file format.")
        sys.exit(1)

    # Filter data
    print("Filtering items with GitHub URLs in 'API_References'...")
    filtered_data = filter_items(data)

    print(f"Found {len(filtered_data)} items with GitHub URLs.")

    # Save data
    print(f"Saving filtered data to '{output_file}'...")
    if output_ext == "json":
        save_json(filtered_data, output_file)
    elif output_ext == "csv":
        save_csv(filtered_data, output_file)
    else:
        print("Error: Unsupported output file format.")
        sys.exit(1)


if __name__ == "__main__":
    main()
