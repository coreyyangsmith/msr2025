import csv
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict
from dateutil.parser import parse as parse_date
from google.cloud import bigquery

from ...utils.config import RQ2_3_OUTPUT, RQ2_3_INPUT

# Set up Google Cloud authentication
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "msr-2025-d058d9631c19.json"

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def run_bigquery_query(query):
    """Run a BigQuery query and return the results."""
    client = bigquery.Client()
    query_job = client.query(query)
    results = query_job.result()
    return results


def get_stars_count(owner, repo):
    """Get the total number of stars for a repository."""
    query = f"""
    SELECT COUNT(*) AS star_count
    FROM `githubarchive.month.*`
    WHERE type = 'WatchEvent'
      AND repo.name = '{owner}/{repo}'
    """
    results = run_bigquery_query(query)
    for row in results:
        return int(row["star_count"])
    return 0


def get_forks_count(owner, repo):
    """Get the total number of forks for a repository."""
    query = f"""
    SELECT COUNT(*) AS fork_count
    FROM `githubarchive.month.*`
    WHERE type = 'ForkEvent'
      AND repo.name = '{owner}/{repo}'
    """
    results = run_bigquery_query(query)
    for row in results:
        return int(row["fork_count"])
    return 0


def get_open_issues_count(owner, repo, end_date):
    """Get the total number of open issues for a repository up to a certain date."""
    query = f"""
    SELECT
      SUM(IF(action = 'opened', 1, IF(action = 'closed', -1, 0))) AS open_issues
    FROM (
      SELECT
        JSON_EXTRACT_SCALAR(payload, '$.action') AS action
      FROM
        `githubarchive.month.*`
      WHERE
        type = 'IssuesEvent'
        AND repo.name = '{owner}/{repo}'
        AND PARSE_DATE('%Y-%m-%d', SUBSTR(created_at, 1, 10)) <= DATE('{end_date}')
    )
    """
    results = run_bigquery_query(query)
    for row in results:
        return int(row["open_issues"])
    return 0


FIELD_PROCESSORS = {
    "bigquery_stars": get_stars_count,
    "bigquery_forks": get_forks_count,
}


def process_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single CSV row to fetch additional GitHub information using BigQuery.

    Args:
        row (Dict[str, Any]): A dictionary representing a row from the CSV.

    Returns:
        Dict[str, Any]: The updated row with new fields.
    """
    owner = row.get("github_owner")
    repo = row.get("github_repo")
    cve_publish_date = row.get("cve_publish_date")

    if not owner or not repo:
        logging.warning(f"Missing owner or repo in row: {row}")
        # Set None for all fields in FIELD_PROCESSORS
        for field_name in FIELD_PROCESSORS:
            row[field_name] = None
        row["github_open_issues"] = None
        return row

    for field_name, func in FIELD_PROCESSORS.items():
        try:
            result = func(owner, repo)
            row[field_name] = result
            logging.info(f"Processed {owner}/{repo}: {field_name} - {result}")
        except Exception as e:
            logging.error(f"Error processing {owner}/{repo} for {field_name}: {e}")
            row[field_name] = None

    # Process github_open_issues
    if cve_publish_date:
        try:
            # Parse end_date using dateutil.parser
            end_date_iso = parse_date(cve_publish_date).date().isoformat()
            open_issues_count = get_open_issues_count(owner, repo, end_date_iso)
            row["github_open_issues"] = open_issues_count
            logging.info(
                f"Processed {owner}/{repo}: github_open_issues - {open_issues_count}"
            )
        except (ValueError, TypeError) as e:
            logging.error(f"Date parsing error for {owner}/{repo}: {e}")
            row["github_open_issues"] = None
    else:
        logging.warning(f"Missing cve_publish_date for {owner}/{repo}.")
        row["github_open_issues"] = None

    return row


def process_csv(input_csv: str, output_csv: str, max_workers: int = 5):
    """
    Read the input CSV, process each repository to fetch additional information, and write to output CSV.

    Args:
        input_csv (str): Path to the input CSV file.
        output_csv (str): Path to the output CSV file.
        max_workers (int): Maximum number of threads for concurrent processing.
    """
    # Read all rows from the input CSV
    with open(input_csv, newline="", encoding="utf-8") as csvfile_in:
        reader = csv.DictReader(csvfile_in)
        fieldnames = reader.fieldnames.copy()
        for field_name in FIELD_PROCESSORS.keys():
            if field_name not in fieldnames:
                fieldnames.append(field_name)
        # Add 'github_open_issues' to fieldnames if not present
        if "github_open_issues" not in fieldnames:
            fieldnames.append("github_open_issues")
        rows = list(reader)

    logging.info(f"Total repositories to process: {len(rows)}")

    # Use ThreadPoolExecutor to process repositories concurrently
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_row = {executor.submit(process_row, row): row for row in rows}

        for future in as_completed(future_to_row):
            row = future_to_row[future]
            try:
                updated_row = future.result()
                # Handle the updated_row if needed
            except Exception as e:
                logging.error(f"Error processing row {row}: {e}")

    # Write the updated rows to the output CSV
    with open(output_csv, "w", newline="", encoding="utf-8") as csvfile_out:
        writer = csv.DictWriter(csvfile_out, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    logging.info(f"Finished processing. Output written to {output_csv}")


def main():
    input_csv = RQ2_3_INPUT
    output_csv = RQ2_3_OUTPUT
    process_csv(input_csv, output_csv)


if __name__ == "__main__":
    main()
