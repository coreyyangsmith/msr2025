"""
This script queries the OSV API to get a list of all affected versions for each CVE.

It performs the following:
1. Reads CVE data from rq0_4_unique_cves.csv
2. For each CVE, queries the OSV API to get affected version ranges and patched version
3. Saves the affected version information to a new CSV file, but only for CVEs that have been patched

Dependencies:
- pandas: For data manipulation
- requests: For API calls
- concurrent.futures: For multithreading
"""

import pandas as pd
import requests
import time
from tqdm import tqdm
import concurrent.futures
import os
from datetime import datetime, timedelta
from src.utils.config import MAX_WORKERS


def get_affected_versions(package_name, ecosystem, cve_id):
    """
    Gets all versions affected by a given CVE using the OSV API.

    Args:
        package_name (str): The name of the package.
        ecosystem (str): The ecosystem of the package (e.g., Maven, npm).
        cve_id (str): The CVE identifier to check against.

    Returns:
        dict: A dictionary containing affected versions, patched version and whether it's patched.
    """
    url = "https://api.osv.dev/v1/query"

    payload = {
        "package": {"name": package_name, "ecosystem": ecosystem},
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while querying {package_name}: {e}")
        return {
            "affected_versions": [],
            "cve_patched": False,
            "patched_version": None,
            "details": str(e),
        }

    # Initialize variables
    affected_versions = []
    cve_patched = False
    vuln_details = None
    patched_version = None

    # Iterate through vulnerabilities
    vulns = data.get("vulns", [])
    for vuln in vulns:
        if cve_id not in vuln.get("aliases", []):
            continue

        for affected in vuln.get("affected", []):
            pkg = affected.get("package", {})
            if pkg.get("name") != package_name:
                continue

            vuln_details = vuln  # Capture the vulnerability details

            # Extract affected versions
            versions = affected.get("versions", [])
            affected_versions.extend(versions)

            # Check for fixed versions in ranges
            ranges = affected.get("ranges", [])
            for range_info in ranges:
                if range_info.get("type") != "ECOSYSTEM":
                    continue
                events = range_info.get("events", [])
                for event in events:
                    if "fixed" in event:
                        cve_patched = True
                        patched_version = event["fixed"]

    return {
        "affected_versions": affected_versions,
        "cve_patched": cve_patched,
        "patched_version": patched_version,
        "details": vuln_details,
    }


def process_cve(row):
    """Process a single CVE row and return the result"""
    cve_id = row["cve_id"]
    group_id = row["group_id"]
    artifact_id = row["artifact_id"]

    if pd.isna(cve_id):
        return None

    if row["cve_patched"] == False:
        return None

    try:
        result = get_affected_versions(f"{group_id}:{artifact_id}", "Maven", cve_id)
        processed_result = {
            "parent_combined_name": row["combined_name"],
            "cve_id": cve_id,
            "affected_version": ",".join(result["affected_versions"])
            if result["affected_versions"]
            else "",
            "patched_version": result["patched_version"]
            if result["patched_version"]
            else "",
        }

        # Save individual result to CSV
        pd.DataFrame([processed_result]).to_csv(
            "data/rq3_1_affected_versions_list.csv",
            mode="a",
            header=not os.path.exists("data/rq3_1_affected_versions_list.csv"),
            index=False,
        )

        time.sleep(0.1)  # Rate limiting
        return processed_result

    except Exception as e:
        print(f"Error processing {cve_id}: {str(e)}")
        return None


# Read the CVE data
print("Reading CVE data...")
df = pd.read_csv("data/rq0_4_unique_cves.csv")

# Clear existing results file
if os.path.exists("data/rq3_1_affected_versions_list.csv"):
    os.remove("data/rq3_1_affected_versions_list.csv")

total_cves = len(df)
print(f"\nProcessing {total_cves} CVE entries...")

# Initialize progress tracking
start_time = datetime.now()
processed_count = 0
results = []

# Create thread pool
with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    # Submit all tasks
    future_to_row = {executor.submit(process_cve, row): row for _, row in df.iterrows()}

    # Process completed tasks with progress bar
    for future in tqdm(
        concurrent.futures.as_completed(future_to_row), total=total_cves
    ):
        processed_count += 1

        # Calculate ETA
        elapsed_time = datetime.now() - start_time
        avg_time_per_item = elapsed_time / processed_count
        remaining_items = total_cves - processed_count
        eta = datetime.now() + (avg_time_per_item * remaining_items)

        # Log progress
        if processed_count % 10 == 0:
            print(f"\nProcessed {processed_count}/{total_cves} CVEs")
            print(f"Elapsed time: {elapsed_time}")
            print(f"Estimated completion: {eta.strftime('%Y-%m-%d %H:%M:%S')}")
            print(
                f"Processing rate: {processed_count/elapsed_time.total_seconds():.2f} CVEs/second"
            )

        try:
            result = future.result()
            if result:
                results.append(result)
        except Exception as e:
            print(f"Error processing task: {str(e)}")

print(f"\nCompleted processing {len(results)} CVEs")
print(f"Total elapsed time: {datetime.now() - start_time}")
print(f"Results saved to data/rq3_1_affected_versions_list.csv")
