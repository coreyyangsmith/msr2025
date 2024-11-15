"""
Hits the Weaver API /artifact endpoint and OSV Dev API
to get info from desired release
"""

import requests
from datetime import datetime
from ..utils.config import REQ_HEADERS, ARTIFACT_RELEASES_URL
from ..utils.parsing import extract_combined_name_from_version_id

"""
What info to include with EnrichedRelease?
"""


class EnrichedRelease:
    def __init__(self, node):
        self.id = node.get("id", "UNKNOWN")
        self.combined_name = extract_combined_name_from_version_id(self.id)
        self.release_version = node.get("version", "UNKNOWN")
        self.release_timestamp = node.get("timestamp", None)
        self.release_date = self.set_release_date()
        self.cves = node.get("cve", [])

    def set_release_date(self):
        if self.release_timestamp is not None:
            # Convert timestamp to datetime object
            release_date = datetime.fromtimestamp(
                self.release_timestamp / 1000
            ).strftime("%Y-%m-%d")
        else:
            release_date = "UNKNOWN"
        return release_date
