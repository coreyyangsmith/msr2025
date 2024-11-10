import csv
import argparse
import re
import sys
from urllib.parse import urlparse


def convert_ssh_to_https(url):
    """
    Convert SSH GitHub URL to HTTPS URL.
    Example:
        git@github.com:acmenlt/dynamic-threadpool.git -> https://github.com/acmenlt/dynamic-threadpool.git
    """
    ssh_pattern = re.compile(r"^git@github\.com:(.+)/(.+)\.git$")
    match = ssh_pattern.match(url)
    if match:
        user_or_org = match.group(1)
        repo = match.group(2)
        https_url = f"https://github.com/{user_or_org}/{repo}.git"
        return https_url
    return url  # Return the original URL if it doesn't match SSH pattern


def is_valid_github_url(url):
    """
    Basic validation to check if the URL is a valid GitHub URL.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False
    if parsed.netloc.lower() != "github.com":
        return False
    return True


def process_csv(input_file, output_file):
    unique_urls = set()
    unique_rows = []

    with open(input_file, mode="r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        # Check if required columns are present
        required_columns = {"groupId", "artifactId", "version", "githubUrl"}
        if not required_columns.issubset(reader.fieldnames):
            print(
                f"Error: Input CSV must contain the following columns: {', '.join(required_columns)}"
            )
            sys.exit(1)

        for row in reader:
            original_url = row["githubUrl"].strip()
            converted_url = convert_ssh_to_https(original_url)
            if not is_valid_github_url(converted_url):
                print(f"Warning: Invalid GitHub URL skipped: {original_url}")
                continue  # Skip invalid URLs

            if converted_url not in unique_urls:
                unique_urls.add(converted_url)
                # Update the githubUrl in the row to the converted URL
                row["githubUrl"] = converted_url
                unique_rows.append(row)
            else:
                print(f"Duplicate URL found and skipped: {converted_url}")

    # Write the unique rows to the output CSV
    with open(output_file, mode="w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["groupId", "artifactId", "version", "githubUrl"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for row in unique_rows:
            writer.writerow(row)

    print(
        f"Processing complete. {len(unique_rows)} unique entries written to '{output_file}'."
    )


def main():
    input_csv = "data/filtered_github_artifacts.csv"
    output_csv = "data/unique_filtered_github_artifacts.csv"

    process_csv(input_csv, output_csv)


if __name__ == "__main__":
    main()
