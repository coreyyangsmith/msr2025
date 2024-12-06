### Generic Parameters ###
NEO4J_URL = "http://localhost:7474/db/neo4j/tx/commit"
NEO4J_AUTH = ("neo4j", "Password1")
NEO4J_BOLT_URL = "bolt://localhost:7687"

ARTIFACT_RELEASES_URL = "http://localhost:8080/artifact/releases"
WEAVER_URL = "https://localhost:8080/cypher"
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
RQ2_1_FILTERED_OUTPUT = "data/rq2_1_github_repositories_by_cve_filtered.csv"
RQ2_1_NON_GITHUB_OUTPUT = "data/rq2_1_github_repositories_by_cve_non_github.csv"
RQ2_1_FAILED_OUTPUT = "data/rq2_1_github_repositories_by_cve_failed.csv"

# RQ2_2 Enrich Data from GitHub API
# RQ2_2_INPUT = RQ2_1_OUTPUT
# RQ2_2_OUTPUT = "data/rq2_2_github_cves_with_gh_metrics.csv"

# RQ2_3 Enrich Data from Google BigQuery
# RQ2_3_INPUT = RQ2_2_OUTPUT
# RQ2_3_OUTPUT = "data/rq2_3_github_cves_with_gh_bq_metrics.csv"

# RQ2_X OpenDigger API
RQ2_OPENDIGGER_INPUT = RQ2_1_FILTERED_OUTPUT
OPENDIGGER_BASE_URL = "https://oss.x-lab.info/open-digger/github"
RQ2_OPENDIGGER_OUTPUT = "data/rq2_x_opendigger/"

# RQ2_3 Extract Repository Names
RQ2_3_INPUT = RQ2_OPENDIGGER_OUTPUT
RQ2_3_OUTPUT = "data/rq2_3_repo_names.csv"

# RQ2_4 OpenDigger API
RQ2_4_INPUT = RQ2_3_OUTPUT
RQ2_4_OUTPUT = RQ2_OPENDIGGER_OUTPUT

# RQ2_5 Summarize Metrics Availability
RQ2_5_INPUT = RQ2_OPENDIGGER_OUTPUT
RQ2_5_OUTPUT = "data/rq2_5_metrics_availability.csv"

# RQ2_6 Clean Metrics Data
RQ2_6_INPUT = RQ2_5_OUTPUT
RQ2_6_OUTPUT = "data/rq2_6_cleaned_metrics_repos.csv"

# RQ2_7 Combine Datasets
RQ2_7_INPUT_METRICS = RQ2_6_OUTPUT
RQ2_7_INPUT_CVES = RQ2_1_FILTERED_OUTPUT
RQ2_7_OUTPUT = "data/rq2_7_combined_datasets.csv"

# RQ2_8 Enrich Metrics Data
RQ2_8_INPUT = RQ2_7_OUTPUT
RQ2_8_OUTPUT = "data/rq2_8_enriched.csv"


# RQ2_10 Filter Non-CVE GitHub Repositories
RQ2_10_INPUT = "data/rq0_2_non_cve_artifacts.csv"
RQ2_10_OUTPUT = "data/rq2_10_github_repositories_no_cve.csv"
RQ2_10_FILTERED_OUTPUT = "data/rq2_10_github_repositories_no_cve_filtered.csv"
RQ2_10_NON_GITHUB_OUTPUT = "data/rq2_10_github_repositories_no_cve_non_github.csv"

RQ11_OPENDIGGER_INPUT = RQ2_10_FILTERED_OUTPUT
RQ11_OPENDIGGER_OUTPUT = "data/rq11_opendigger/"

RQ12_OPENDIGGER_INPUT = RQ11_OPENDIGGER_OUTPUT
RQ12_OUTPUT = "data/rq2_13_non_cve_gh_repo_names.csv"

RQ2_13_INPUT = RQ12_OUTPUT
RQ2_13_OPENDIGGER_OUTPUT = RQ11_OPENDIGGER_OUTPUT

RQ14_OPENDIGGER_INPUT = RQ2_13_OPENDIGGER_OUTPUT
RQ14_FILE_INPUT = RQ12_OUTPUT
RQ14_OUTPUT = "data/rq2_14_metrics_availability.csv"

RQ2_15_INPUT = RQ14_OUTPUT
RQ2_15_OUTPUT = "data/rq2_15_cleaned_metrics_repos.csv"

# RQ 16
RQ2_16_INPUT_METRICS = RQ2_15_OUTPUT
RQ2_16_INPUT_CVES = RQ2_10_FILTERED_OUTPUT
RQ2_16_OUTPUT = "data/rq2_16_combined_datasets.csv"

RQ2_17_INPUT = RQ2_16_OUTPUT
RQ2_17_OUTPUT = "data/rq2_17_enriched.csv"

OPENDIGGER_VALUES = [
    "issues_new",
    "issues_closed",
    "issue_comments",
    "issue_response_time",
    "issue_resolution_duration",
    "issue_age",
    "code_change_lines_add",
    "code_change_lines_remove",
    "code_change_lines_sum",
    "change_requests",
    "change_requests_accepted",
    "change_requests_reviews",
    "change_request_response_time",
    "change_request_resolution_duration",
    "change_request_age",
    "bus_factor",
    "inactive_contributors",
    "activity",
    "new_contributors",
    "attention",
    "stars",
    "technical_fork",
    "participants",
    "openrank",
]

####################
### RQ3 Pipeline ###
####################

# RQ3_1


### DATA ANALYSIS
RQ0_BAR_PLOT_CVE_SEVERITY_INPUT = RQ0_4_OUTPUT_UNIQUE_CVES


## RQ1 - MEAN TIME TO MITIGATE BY SEVERITY
MTTM_UNIT = "days"
RQ1_MTTM_INPUT = RQ0_4_OUTPUT_UNIQUE_CVES


# MAVEN API CONFIG
MAVEN_POM_RETRIES = 1
# BACKOFF IS EXPONENTIAL backoff=*2
BACKOFF_STARTING_TIME_IN_SECONDS = 1
BACKOFF_FACTOR = 1


# HARDWARE CONFIG
MAX_WORKERS = 96
