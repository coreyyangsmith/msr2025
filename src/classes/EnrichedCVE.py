"""
Hits the Weaver API /artifact endpoint and OSV Dev API
to get info from desired release
"""

import requests
from datetime import datetime
from ..utils.config import REQ_HEADERS, ARTIFACT_RELEASES_URL

"""
What info to include with EnrichedRelease?
    """


class EnrichedCVE:
    def __init__(self, cve):
        self.id = cve.get("name", "UNKNOWN")
        self.severity = cve.get("severity", "UNKNOWN").upper()

    def set_release_date(release_timestamp):
        if release_timestamp is not None:
            # Convert timestamp to datetime object
            release_date = datetime.fromtimestamp(release_timestamp / 1000).strftime(
                "%Y-%m-%d"
            )
        else:
            release_date = "UNKNOWN"
        return release_date

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
