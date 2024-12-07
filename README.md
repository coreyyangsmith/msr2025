 // Start of Selection
# MSR 2025 - Dependency Mining Challenge

## Setup Instructions

1. **Install required dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

## Dataset
Our dataset is hosted on a Neo4j instance and contains 658,078 artifacts. Vulnerability data is extraction from OSV.dev on November 30th, 2024. For our initial data import, we use the `goblin_maven_2024_08_30.dump` dataset provided by the organizers. We run our queries using Neo4j version 4.4.4. We leverage Goblin Weaver API (v2.1.0) to extract additional information about the artifacts and releases, pertaining to CVEs, and use Goblin Weaver 

Our entire dataset and pipeline is hosted on Zenodo and can be found [here]().

## RQ0: Data Extraction and Processing
RQ0 contains our preliminary data processing and aims to extract high-level statistics and information about our dataset.

After setting up the project by adjusting the API links and number of workers, from the `src/utils/config.py` file, we can run the following scripts in sequence to extract our initial dataset:

Step 1: Extract all Artifacts
* `python -m src.data_extraction.rq0.1_extract_artifact_names_from_api`
* Extract all artifact names from the API and save to `data/rq0_1_all_artifacts.csv`
* Uses Neo4J Instance

Step 2: Enrich Artifact Data
* `python -m src.data_extraction.rq0.2_enrich_artifact_data`p
* Enrich the artifact data with additional information pertaining to CVEsand save to `data/rq0_2_enriched_artifacts.csv`
* Uses Neo4J Instance and Goblin Weaver API

Step 3: Extract Releases and CVES
* `python -m src.data_extraction.rq0.3_extract_releases_cves`
* Extract all releases and CVES for each release and save to `data/rq0_3_releases_with_cves.csv`
* Uses Neo4J Instance and Goblin Weaver API

Step 4: Extract Unique CVES
* `python -m src.data_extraction.rq0.4_extract_unique_cves`
* Extract all unique CVES and save to `data/rq0_4_unique_cves.csv`

All data processed throughout these scripts is stored in the `data/` directory.

## RQ1: Life Cycle of Vulnerabilities

RQ1 investigates the life cycle of vulnerabilities in our dataset. We run the following scripts in sequence:

Step 1: Calculate Unique CVE by Severity
* `python -m src.data_analysis.rq0.table_1_unique_cve_by_severity`

Step 2: Calculate Mean Time to Mitigate
* `python -m src.data_analysis.rq1.table2_mean_time_to_mitigate`

****

## RQ2: Project Characteristics Correlation

RQ2 investigates the correlation between project characteristics and vulnerability life cycle. We run the following scripts in sequence for data extraction:

Step 1: Find GitHub-hosted repositories from Maven POM.xml.
* `python -m src.data_extraction.rq2.1_filter_github_repositories`

Step 2: Get GitHub Repository Data from OpenDigger
* `python -m src.data_extraction.rq2.2_opendigger_api`
* `python -m src.data_extraction.rq2.3_extract_folder_names`
* `python -m src.data_extraction.rq2.4_opendigger_api`

Step 3: Data Cleaning
* `python -m src.data_extraction.rq2.5_summarize_metrics`
* `python -m src.data_extraction.rq2.6_clean_data`
* `python -m src.data_extraction.rq2.7_combine_datasets`
* `python -m src.data_extraction.rq2.8_enrich_metrics_data`
* `python -m src.data_extraction.rq2.9_clean_data`

Step 4: Repeat for non-CVE repositories
* `python -m src.data_extraction.rq2.10_filter_non_cve_github_repositories`
* `python -m src.data_extraction.rq2.11_opendigger_api`
* `python -m src.data_extraction.rq2.12_extract_folder_names`
* `python -m src.data_extraction.rq2.13_opendigger_api`
* `python -m src.data_extraction.rq2.14_summarize_metrics`
* `python -m src.data_extraction.rq2.15_clean_data`
* `python -m src.data_extraction.rq2.16_combine_datasets`
* `python -m src.data_extraction.rq2.17_enrich_metrics_data`
* `python -m src.data_extraction.rq2.18_clean_data`

Step 5: Calculate Correlation between Project Characteristics and Vulnerability Life Cycle
* `python -m src.data_analysis.rq2.1_point_biserial_correlation`

## RQ3: Dependent Package Patching Strategy

RQ3 investigates the patching strategy of dependent packages. We run the following scripts in sequence:

Step 1: Extract Affected Releases
* `python -m src.data_extraction.rq3.1_extract_affected_versions_list`

Step 2: Extract Dependent Artifacts from Releases
* `python -m src.data_extraction.rq3.2_dependent_artifacts_from_release`

Step 3: Get Dependent Releases List
* `python -m src.data_extraction.rq3.3_get_releases`

Step 4: Analysis
* `python -m src.data_analysis.rq3.1_get_class_split`
* `python -m src.data_analysis.rq3.2_analyze_class_split`
* `python -m src.data_analsysis.rq3.6_box_plot`