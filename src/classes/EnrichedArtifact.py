"""
Hits the Weaver API /artifact endpoint
to get info from desired artifact
"""

import requests
from datetime import datetime


class EnrichedArtifact:
    def __init__(self, artifact_name: str):
        self.url = "http://localhost:8080/artifact/releases"
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self.group_id = artifact_name.split(":")[0]
        self.artifact_id = artifact_name.split(":")[1]
        self.query = {
            "groupId": self.group_id,
            "artifactId": self.artifact_id,
            "addedValues": ["CVE"],
        }
        self.nodes = (
            requests.post(url=self.url, json=self.query, headers=self.headers)
            .json()
            .get("nodes", [])
        )

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

    def get_cve_lifetimes(self):
        cve_lifetimes = {}
        for node in self.nodes:
            timestamp = node.get("timestamp", None)
            if timestamp is None:
                continue
            # Convert timestamp to datetime object for better readability
            date = datetime.fromtimestamp(timestamp / 1000)
            cves = node.get("cve", [])
            version = node.get("version", "UNKNOWN")
            for cve in cves:
                severity = cve.get("severity", "UNKNOWN").upper()
                cve_name = cve.get("name", "UNKNOWN")
                if cve_name not in cve_lifetimes:
                    # Initialize with start and end date being the current date
                    cve_lifetimes[cve_name] = {
                        "severity": severity,
                        "start": date,
                        "end": date,
                        "start_version": version,
                        "end_version": version,
                    }
                else:
                    # Update start and end dates, and versions
                    if date < cve_lifetimes[cve_name]["start"]:
                        cve_lifetimes[cve_name]["start"] = date
                        cve_lifetimes[cve_name]["start_version"] = version
                    if date > cve_lifetimes[cve_name]["end"]:
                        cve_lifetimes[cve_name]["end"] = date
                        cve_lifetimes[cve_name]["end_version"] = version

        # After calculating start and end dates, calculate durations
        for cve_name, times in cve_lifetimes.items():
            duration = times["end"] - times["start"]
            times["duration"] = duration
        return cve_lifetimes

    # cve_lifetimes = cve_manager.get_cve_lifetimes()
    # print(cve_lifetimes)
    # # Print the lifetimes
    # for cve_name, times in cve_lifetimes.items():
    #     start_date = times["start"].strftime("%Y-%m-%d")
    #     end_date = times["end"].strftime("%Y-%m-%d")
    #     duration_days = times["duration"].days
    #     print(
    #         f"CVE {cve_name} lifetime: {start_date} to {end_date}, duration: {duration_days} days"
    #     )
