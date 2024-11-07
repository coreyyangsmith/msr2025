### Generic Parameters ###
NEO4J_URL = "http://localhost:8080/cypher"
ARTIFACT_RELEASES_URL = "http://localhost:8080/artifact/releases"
GITHUB_API_URL = "https://api.github.com"

ECOSYSTEM = "Maven"
REQ_HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}
GITHUB_HEADERS = {"Accept": "application/vnd.github.v3+json"}

### META DATA
### FILL THIS OUT FOR EACH RUN
### CURRENT DB RUN Saturday November 3rd 1:36pm MST

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
FILTER_FOR_INVALID_DATA = True
RQ0_4_INPUT = RQ0_2_OUTPUT_ARTIFACTS_CVES
RQ0_4_OUTPUT_UNIQUE_CVES = "data/rq0_4_unique_cves.csv"

####################
### RQ2 Pipeline ###
####################

# RQ2_1 Filter GitHub Hosted Repositories
RQ2_1_INPUT = RQ0_4_OUTPUT_UNIQUE_CVES
RQ2_1_OUTPUT = "data/rq2_1_github_repositories_by_cve.csv"

# RQ2_2 Enrich Data from GitHub API
RQ2_2_INPUT = RQ2_1_OUTPUT
RQ2_2_OUTPUT = "data/rq2_2_github_cves_with_gh_metrics.csv"

# RQ2_3 Enrich Data from Google BigQuery
RQ2_3_INPUT = RQ2_2_OUTPUT
RQ2_3_OUTPUT = "data/rq2_3_github_cves_with_gh_bq_metrics.csv"

# RQ2_X OpenDigger API
RQ2_OPENDIGGER_INPUT = RQ2_1_OUTPUT
OPENDIGGER_BASE_URL = "https://oss.x-lab.info/open-digger/github"
RQ2_OPENDIGGER_OUTPUT = "data/rq2_x_opendigger/"

####################
### RQ3 Pipeline ###
####################

# RQ3_1


### DATA ANALYSIS
RQ0_BAR_PLOT_CVE_SEVERITY_INPUT = RQ0_4_OUTPUT_UNIQUE_CVES


## RQ1 - MEAN TIME TO MITIGATE BY SEVERITY
MTTM_UNIT = "days"
RQ1_MTTM_INPUT = RQ0_4_OUTPUT_UNIQUE_CVES
