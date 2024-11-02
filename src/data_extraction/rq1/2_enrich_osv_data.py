import requests
import csv
import os


def check_cve_for_release(package_name, ecosystem, version, cve_id):
    """
    Checks if a specific package version is affected by a given CVE using the OSV API.

    Args:
        package_name (str): The name of the package.
        ecosystem (str): The ecosystem of the package (e.g., Maven, npm).
        version (str): The version of the package to check.
        cve_id (str): The CVE identifier to check against.

    Returns:
        dict: A dictionary containing whether the package is affected, the severity, and additional details.
    """
    url = "https://api.osv.dev/v1/query"

    payload = {
        "version": version,
        "package": {"name": package_name, "ecosystem": ecosystem},
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while querying {package_name} {version}: {e}")
        return {"affected": False, "severity": None, "details": str(e)}

    # Check if the CVE ID is in the results
    vulns = data.get("vulns", [])
    for vuln in vulns:
        if cve_id in vuln.get("aliases", []):
            severity = None
            # Extract severity if available
            if "severity" in vuln:
                severity = vuln["severity"]
            return {"affected": True, "severity": severity, "details": vuln}

    return {"affected": False, "severity": None, "details": None}


def parse_artifact(artifact):
    """
    Parses the Artifact field to extract ecosystem and package name.

    Assumes Artifact is in the format 'ecosystem:package_name'.
    Adjust this function based on the actual format of the Artifact field.

    Args:
        artifact (str): The artifact string.

    Returns:
        tuple: A tuple containing (ecosystem, package_name). Returns (None, None) if parsing fails.
    """
    try:
        ecosystem = "Maven"
        return ecosystem, artifact
    except ValueError:
        print(
            f"Artifact '{artifact}' is not in the expected 'ecosystem:package_name' format."
        )
        return None, None


def process_cve_lifetimes(input_file, output_file):
    """
    Processes the cve_lifetimes CSV file, checks each CVE against the OSV API, and writes the results to a new CSV.

    Args:
        input_file (str): Path to the input CSV file.
        output_file (str): Path to the output CSV file.
    """
    if not os.path.exists(input_file):
        print(f"Input file '{input_file}' does not exist.")
        return

    with open(input_file, newline="", encoding="utf-8") as csvfile_in, open(
        output_file, "w", newline="", encoding="utf-8"
    ) as csvfile_out:
        reader = csv.DictReader(csvfile_in)

        # Define new fieldnames for the output, adding individual API components
        new_fields = [
            "API_ID",
            "API_Summary",
            "API_Details",
            "API_Aliases",
            "API_Modified",
            "API_Published",
            "API_Severity",
            "API_CWE_IDs",
            "API_NVD_Published_At",
            "API_GitHub_Reviewed",
            "API_Affected_Package_Name",
            "API_Affected_Ecosystem",
            "API_Affected_Versions",
            "API_References",
        ]
        fieldnames = reader.fieldnames + new_fields

        writer = csv.DictWriter(csvfile_out, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            artifact = row.get("Artifact")
            cve_id = row.get("CVE_ID")
            version = row.get("End Version")  # or another version field as appropriate

            ecosystem, package_name = parse_artifact(artifact)
            if not ecosystem or not package_name:
                # If parsing failed, skip to the next row
                row.update({field: "" for field in new_fields})
                row["API_Affected"] = "Parsing Error"
                writer.writerow(row)
                continue

            # Optionally, decide which version to check; here using End Version
            print(package_name, ecosystem, version, cve_id)
            api_result = check_cve_for_release(package_name, ecosystem, version, cve_id)

            if "details" in api_result:
                flattened_details = flatten_api_details(api_result["details"])
                row.update(flattened_details)

            writer.writerow(row)

            print(
                f"Processed {artifact} {version} for {cve_id}: Affected={api_result.get('affected')}"
            )


# Flatten API_Details into individual components
def flatten_api_details(api_details):
    # Check if api_details is None before proceeding
    if api_details is None:
        # Return empty fields if the details are missing
        return {
            key: ""
            for key in [
                "API_ID",
                "API_Summary",
                "API_Details",
                "API_Aliases",
                "API_Modified",
                "API_Published",
                "API_Severity",
                "API_CWE_IDs",
                "API_NVD_Published_At",
                "API_GitHub_Reviewed",
                "API_Affected_Package_Name",
                "API_Affected_Ecosystem",
                "API_Affected_Versions",
                "API_References",
            ]
        }

    try:
        flattened = {
            "API_ID": api_details.get("id", ""),
            "API_Summary": api_details.get("summary", ""),
            "API_Details": api_details.get("details", ""),
            "API_Aliases": ", ".join(api_details.get("aliases", [])),
            "API_Modified": api_details.get("modified", ""),
            "API_Published": api_details.get("published", ""),
            "API_Severity": api_details["database_specific"].get("severity", ""),
            "API_CWE_IDs": ", ".join(
                api_details["database_specific"].get("cwe_ids", [])
            ),
            "API_NVD_Published_At": api_details["database_specific"].get(
                "nvd_published_at", ""
            ),
            "API_GitHub_Reviewed": api_details["database_specific"].get(
                "github_reviewed", ""
            ),
            "API_Affected_Package_Name": api_details["affected"][0]["package"].get(
                "name", ""
            )
            if api_details.get("affected")
            else "",
            "API_Affected_Ecosystem": api_details["affected"][0]["package"].get(
                "ecosystem", ""
            )
            if api_details.get("affected")
            else "",
            "API_Affected_Versions": ", ".join(
                api_details["affected"][0].get("versions", [])
            )
            if api_details.get("affected")
            else "",
            "API_References": ", ".join(
                [ref.get("url", "") for ref in api_details.get("references", [])]
            ),
        }
    except KeyError as e:
        print(
            f"KeyError encountered: {e}. Some fields might be missing in the API response."
        )
        flattened = {
            key: ""
            for key in [
                "API_ID",
                "API_Summary",
                "API_Details",
                "API_Aliases",
                "API_Modified",
                "API_Published",
                "API_Severity",
                "API_CWE_IDs",
                "API_NVD_Published_At",
                "API_GitHub_Reviewed",
                "API_Affected_Package_Name",
                "API_Affected_Ecosystem",
                "API_Affected_Versions",
                "API_References",
            ]
        }
    return flattened


if __name__ == "__main__":
    input_file = "data/rq1_cve_lifetimes.csv"
    output_file = "data/rq1_cve_lifetimes_updated.csv"
    process_cve_lifetimes(input_file, output_file)
