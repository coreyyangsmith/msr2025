"""
Hits the Weaver API /artifact endpoint
to get info from desired artifact
"""

import requests
import time
from datetime import datetime

from ..utils.config import REQ_HEADERS, ARTIFACT_RELEASES_URL, WEAVER_URL, ECOSYSTEM
from ..utils.time_conversion import (
    convert_datetime_to_timestamp_numbers,
    convert_timestamp_numbers_to_datetime,
)
from .EnrichedRelease import EnrichedRelease
from .EnrichedCVE import EnrichedCVE


class EnrichedArtifact:
    def __init__(self, combined_name: str):
        self.url = ARTIFACT_RELEASES_URL
        self.headers = REQ_HEADERS
        self.combined_name = combined_name
        self.group_id = combined_name.split(":")[0]
        self.artifact_id = combined_name.split(":")[1]

        self.query = {
            "groupId": self.group_id,
            "artifactId": self.artifact_id,
            "addedValues": ["CVE"],
        }

        self.latest_release_cypher_query = f"""
        MATCH (a:Artifact {{id: '{combined_name}'}})
        OPTIONAL MATCH (a)-[:relationship_AR]->(r:Release)
        WITH a, r
        ORDER BY r.timestamp DESC
        WITH a, COLLECT(r)[0] AS latestRelease
        RETURN a.id AS artifactId,
            latestRelease.id AS releaseId,
            latestRelease.timestamp AS releaseTimestamp,
            latestRelease.version AS releaseVersion
        """

        # Nodes represent Releases
        self.nodes = (
            requests.post(url=self.url, json=self.query, headers=self.headers)
            .json()
            .get("nodes", [])
        )

        self.latest_release = self.get_latest_release()

    def get_releases_with_cve(self):
        releases_with_cves = 0
        for node in self.nodes:
            cves = node.get("cve", [])
            if len(cves) > 0:
                releases_with_cves += 1
        return releases_with_cves

    def get_total_cves(self):
        total_cves = 0
        for node in self.nodes:
            cves = node.get("cve", [])
            total_cves += len(cves)
        return total_cves

    def get_total_releases(self):
        return len(self.nodes)

    def get_severity_counts(self):
        severity_counts = {
            "LOW": 0,
            "MODERATE": 0,
            "HIGH": 0,
            "CRITICAL": 0,
            "UNKNOWN": 0,
        }
        for node in self.nodes:
            cves = node.get("cve", [])
            for cve in cves:
                severity = cve.get("severity", "UNKNOWN").upper()
                if severity in severity_counts:
                    severity_counts[severity] += 1
                else:
                    print(f"Severity not found: {severity}")
        return severity_counts

    def is_latest_release(self, version):
        if self.latest_release == version:
            return False
        return True

    def get_latest_release(self):
        query_payload = {
            "query": self.latest_release_cypher_query,
            "addedValues": [],
        }
        response = requests.post(
            url=WEAVER_URL, json=query_payload, headers=self.headers
        )
        data = response.json()
        if "values" in data:
            for item in data["values"]:
                if item.get("releaseVersion") is not None:
                    return item.get("releaseVersion")
        else:
            return None

    def get_cve_lifetimes(self):
        cve_lifetimes = {}
        # Sort the releases by timestamp to process them chronologically
        nodes_sorted = sorted(
            self.nodes, key=lambda x: EnrichedRelease(x).release_timestamp
        )
        # Keep track of CVEs that are currently active
        active_cves = set()

        for node in nodes_sorted:
            enriched_release = EnrichedRelease(node)
            if enriched_release.release_timestamp is None:
                continue

            # Extract CVE IDs directly from the release's CVEs
            current_release_cves = set([cve["name"] for cve in enriched_release.cves])

            # Process CVEs present in the current release
            for cve_id in current_release_cves:
                if cve_id not in cve_lifetimes:
                    # Hit OSV Dev to Extract Additional Information
                    ecosystem = ECOSYSTEM
                    version = enriched_release.release_version
                    api_result = check_cve_for_releases(
                        self.combined_name, ecosystem, version, cve_id
                    )
                    flattened_results = flatten_api_details(api_result["details"])
                    cve_publish_date = flattened_results["API_Published"]
                    api_id = flattened_results["API_ID"]
                    api_aliases = flattened_results["API_Aliases"]
                    # Extract severity from the API results
                    severity = flattened_results.get("API_Severity")

                    # Initialize CVE lifetime information
                    cve_lifetimes[cve_id] = {
                        "severity": severity,
                        "start_version": enriched_release.release_version,
                        "start_version_timestamp": enriched_release.release_timestamp,
                        "start_version_date": enriched_release.release_date,
                        "end_version": enriched_release.release_version,
                        "end_version_timestamp": enriched_release.release_timestamp,
                        "end_version_date": enriched_release.release_date,
                        "cve_publish_date": cve_publish_date,
                        "api_id": api_id,
                        "api_aliases": api_aliases,
                        "patched_version_timestamp": None,
                        "patched_version": None,
                    }
                    active_cves.add(cve_id)
                else:
                    # Update end timestamp and version for the CVE
                    if (
                        enriched_release.release_timestamp
                        > cve_lifetimes[cve_id]["end_version_timestamp"]
                    ):
                        cve_lifetimes[cve_id]["end_version_timestamp"] = (
                            enriched_release.release_timestamp
                        )
                        cve_lifetimes[cve_id]["end_version"] = (
                            enriched_release.release_version
                        )
                        cve_lifetimes[cve_id]["end_version_date"] = (
                            enriched_release.release_date
                        )
                    active_cves.add(cve_id)

            # Identify CVEs that are no longer present (patched) in the current release
            cves_to_remove = []
            for cve_id in active_cves:
                if cve_id not in current_release_cves:
                    # Record the current release as the patched version
                    # I think this needs to be rewritten
                    if cve_lifetimes[cve_id]["patched_version_timestamp"] is None:
                        cve_lifetimes[cve_id]["patched_version_timestamp"] = (
                            enriched_release.release_timestamp
                        )
                        cve_lifetimes[cve_id]["patched_version"] = (
                            enriched_release.release_version
                        )
                        cve_lifetimes[cve_id]["patched_version_date"] = (
                            enriched_release.release_date
                        )
                    cves_to_remove.append(cve_id)

            # Remove patched CVEs from the active set
            for cve_id in cves_to_remove:
                active_cves.remove(cve_id)

        # Calculate durations after processing all releases
        for cve_id, data in cve_lifetimes.items():
            # Check cve_publish_date
            if data["cve_publish_date"] == "" or None:
                print(f"Missing Publish Date for {cve_id}")
                continue

            if data["patched_version_timestamp"] is not None:
                # Duration until the CVE was patched
                duration = int(data["patched_version_timestamp"]) - int(
                    convert_datetime_to_timestamp_numbers(data["cve_publish_date"])
                )
            else:
                current_time_millis = int(time.time() * 1000)
                duration = current_time_millis - int(
                    convert_datetime_to_timestamp_numbers(data["cve_publish_date"])
                )

            data["duration"] = duration

        return cve_lifetimes


def check_cve_for_releases(package_name, ecosystem, version, cve_id):
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
