### Generic Parameters ###
NEO4J_URL = "http://localhost:8080/cypher"
ARTIFACT_RELEASES_URL = "http://localhost:8080/artifact/releases"
ECOSYSTEM = "Maven"
REQ_HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}

### META DATA
### FILL THIS OUT FOR EACH RUN
### CURRENT DB RUN Saturday November 2nd 1:36pm MST

####################
### RQ0 Pipeline ###
####################

# RQ0_1 Extract Artifact List
"""Parsing Artifacts"""
MAX_ARTIFACTS = 1000000  # Expected 658,078 artifacts in goblin_maven_30_08_24.dump
ARTIFACTS_REQ_BATCH_SIZE = 10000  # adjust based on available RAM
RQ0_1_OUTPUT_FILENAME = "data/rq0_1_all_artifacts.csv"

# RQ0_2 Extract Artifacts CVE Data
"""Enrich Artifacts with CVEs"""
FILTER_FOR_CVES = True
FILTER_FOR_UNKNOWN_SEVERITY = True
RQ0_2_INPUT = RQ0_1_OUTPUT_FILENAME
RQ0_2_OUTPUT_ARTIFACTS_CVES = "data/rq0_2_artifacts_cve_releases_count.csv"

# RQ0_3 Extract Releases CVE Data
"""Enrich Releases with CVEs"""
FILTER_FOR_UNKNOWN_CVE_ID = True
RQ0_3_INPUT = RQ0_2_OUTPUT_ARTIFACTS_CVES
RQ0_3_OUTPUT_RELEASES_CVES = "data/rq0_3_releases_cves.csv"

# RQ0_4 Extract Unique CVEs Data
"""Extract Unique CVEs Data"""
RQ0_4_INPUT = RQ0_2_OUTPUT_ARTIFACTS_CVES
RQ0_4_OUTPUT_UNIQUE_CVES = "data/rq0_4_unique_cves.csv"
