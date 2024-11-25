import pandas as pd
import logging
from datetime import datetime
from packaging import version
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import xml.etree.ElementTree as ET

"""
This script analyzes when dependencies adopt patched versions by comparing version numbers.
It reads CVE data and dependency version history to find the first version that upgrades
past a patched version.

Tasks:
1. Reads CVE data and dependency version history files
2. For each dependency:
   - Gets the patched version from CVE data
   - Finds the first version after the patched version in version history
3. Saves results showing when dependencies adopted patched versions

Dependencies:
- pandas
- packaging

Input files:
- data/rq0_4_unique_cve.csv: CVE vulnerability data
- data/rq3_4_dependent_versions.csv: Version history for dependencies

Output:
- data/rq3_5_adoption_dates.csv: When dependencies adopted patched versions
"""


def parse_version(ver_str):
    """Safely parse version string to comparable version object."""
    try:
        return version.parse(ver_str)
    except version.InvalidVersion:
        return None


def find_first_patched_version(versions, patched_version, group_id, artifact_id):
    """
    Find first version that adopts the patched version by checking Maven POM files.

    Args:
        versions: List of version strings
        patched_version: Version that fixed vulnerability
        group_id: Group ID of the dependency to check
        artifact_id: Artifact ID of the dependency to check

    Returns:
        First version that adopts >= patched_version, or None if not found
    """
    if not patched_version:
        return None

    parsed_patched = parse_version(patched_version)
    if not parsed_patched:
        return None

    # Setup session for Maven API requests
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=0.1)
    session.mount("https://", HTTPAdapter(max_retries=retries))

    valid_versions = []
    for ver in versions:
        # Get POM from Maven Central
        pom_url = f"https://repo1.maven.org/maven2/{group_id.replace('.','/')}/{artifact_id}/{ver}/{artifact_id}-{ver}.pom"
        print(f"Checking {pom_url}")
        try:
            response = session.get(pom_url)
            response.raise_for_status()

            # Parse POM XML
            pom = ET.fromstring(response.content)
            ns = {"maven": "http://maven.apache.org/POM/4.0.0"}

            # Check dependencies section
            deps = pom.findall(".//maven:dependencies/maven:dependency", ns)
            for dep in deps:
                dep_group = dep.find("maven:groupId", ns)
                dep_artifact = dep.find("maven:artifactId", ns)
                dep_version = dep.find("maven:version", ns)

                if (
                    dep_group is not None
                    and dep_artifact is not None
                    and dep_version is not None
                    and dep_group.text == group_id
                    and dep_artifact.text == artifact_id
                ):
                    parsed_ver = parse_version(dep_version.text)
                    if parsed_ver and parsed_ver >= parsed_patched:
                        valid_versions.append((parsed_ver, ver))
                        break

        except Exception as e:
            logging.warning(f"Error fetching POM for {ver}: {str(e)}")
            continue

    if not valid_versions:
        return None

    # Return earliest version that adopted patched version
    valid_versions.sort(key=lambda x: x[0])
    return valid_versions[0][1]


def analyze_adoption():
    """Main function to analyze when dependencies adopted patched versions."""

    # Read input data
    logging.info("Reading input files...")
    cve_df = pd.read_csv("data/rq0_4_unique_cves.csv")
    versions_df = pd.read_csv("data/rq3_4_dependent_versions.csv")

    results = []

    # Process each dependency
    for _, row in versions_df.iterrows():
        parent = row["parent"]
        dependent = row["dependent"]
        version_list = (
            row["dependent_versions"].strip('"').strip().split(";")
            if pd.notna(row["dependent_versions"])
            else []
        )
        print(f"Checking {dependent} for versions {version_list}")

        # Find matching CVE by combined name (group_id:artifact_id)
        cve_match = cve_df[cve_df["combined_name"] == parent]
        if len(cve_match) == 0:
            continue

        for _, cve_row in cve_match.iterrows():
            print(f"Checking {dependent} for CVE {cve_row['cve_id']}")
            patched_version = cve_row["patched_version"]
            print(f"Checking {dependent} for patched version {patched_version}")
            first_patched = find_first_patched_version(
                version_list,
                patched_version,
                dependent.split(":")[0],
                dependent.split(":")[1],
            )

            if first_patched:
                results.append(
                    {
                        "dependent": dependent,
                        "cve_id": cve_row["cve_id"],
                        "patched_version": patched_version,
                        "first_adopted_version": first_patched,
                    }
                )

    # Save results
    results_df = pd.DataFrame(results)
    output_path = "data/rq3_5_adoption_dates.csv"
    results_df.to_csv(output_path, index=False)
    logging.info(f"Results saved to {output_path}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("rq3_adoption_dates.log"),
            logging.StreamHandler(),
        ],
    )

    analyze_adoption()
