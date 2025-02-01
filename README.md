# MSR 2025 - Dependency Mining Challenge

Please find our dataset hosted on Zenodo [here](https://zenodo.org/records/14291858).

## Setup Instructions

1. **Install required dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

## Dataset
Our dataset is hosted on a Neo4j instance and contains 658,078 artifacts. Vulnerability data is extraction from OSV.dev on November 30th, 2024. For our initial data import, we use the `goblin_maven_2024_08_30.dump` dataset provided by the organizers. We run our queries using Neo4j version 4.4.4. We leverage Goblin Weaver API (v2.1.0) to extract additional information about the artifacts and releases, pertaining to CVEs, and use Goblin Weaver 

Our entire dataset is hosted on Zenodo and can be found [here](https://zenodo.org/records/14291858).

## Project Structure

The project is structured as follows:

- `data/`: Contains the intermediary datasets, producing by running each script, for the project.
- `src/`: Contains the source code for the project.
- `src/classes`: Contains defined helper classes for the project, abstracting away some complexity for vulnerability lifecycle calculations and API calls.
- `src/data_analysis`: Contains the scripts for the data analysis for the project, split by each RQ.
- `src/data_extraction`: Contains the scripts for the data extraction and processing for the project, split by each RQ.
- `src/utils`: Contains the helper functions and configuration for the project.
- `data_pipeline.drawio`: Contains a visual representation of the data pipeline and metadata information about each dataset. Open with [draw.io](http://draw.io).

Each file (except for those in /utils) contains a prefix that indicates additional information about the script. 

For files in `src/data_extraction`, the prefix indicates the step number in sequence for the data pipeline (i.e. `1_extract_artifact_names_from_api.py` is the first step in the data pipeline for the containing folder RQ0).

For files in `src/data_analysis`, the prefix corresponds to the table or figure number in the report (i.e. `table2_mean_time_to_mitigate.py` corresponds to Table 2 in the report). Finally, there are some extraneous scripts that are not part of the data pipeline or final report, but are useful for debugging or further analysis of the data and dataset. These files are prefixed with `extra_`.

## Running the Scripts
The scripts are setup as a data pipeline. Each script is designed to be run in sequence, with the output of each script being the input to future steps. For a visual representation of the data pipeline, as well as metadata information about each dataset, please refer to the `data_pipeline.md` file.

Keep in mind that some scripts require a local instance of Neo4j and the Goblin Weaver API to be running. Additionally, some scripts hit external APIs and may be rate limited during execution.

The execution of these scripts will take a few hours to complete in full, and each stage must be started from the terminal. The purpose of breaking down each script was for an easier developer experience, debugging, and analysis during the development of this project.

Finally, `src/utils/config.py` contains the API links and number of workers for each script, which can be adjusted accordingly considering the user's systems available resources. `src/utils/` also contains some helper functions used throughout the project for parsing, conversion, and IO operations.

# Addressing the RQs
## RQ0: Data Extraction and Processing
RQ0 contains our preliminary data processing and aims to extract high-level statistics and information about the goblin dataset.

After setting up the project by adjusting the API links and number of workers, from the `src/utils/config.py` file, we can run the following scripts in sequence to extract our initial dataset:

Step 1: Extract all Artifacts
* `python -m src.data_extraction.rq0.1_extract_artifact_names_from_api`
* Extract all artifact names from the API and save to `data/rq0_1_all_artifacts.csv`
* Uses Neo4J Instance

Step 2: Enrich Artifact Data
* `python -m src.data_extraction.rq0.2_enrich_artifact_data`
* Enrich the artifact data with additional information pertaining to CVEsand save to `data/rq0_2_artifacts_cve_releases_count.csv`
* Uses Neo4J Instance and Goblin Weaver API

Step 3: Extract Releases and CVES
* `python -m src.data_extraction.rq0.3_extract_releases_cves`
* Extract all releases and CVES for each release and save to `data/rq0_3_releases_with_cves.csv`
* Uses Neo4J Instance and Goblin Weaver API

Step 4: Extract Unique CVES
* `python -m src.data_extraction.rq0.4_extract_unique_cves`
* Extract all unique CVES and save to `data/rq0_4_unique_cves.csv`
* Uses Neo4J Instance and Goblin Weaver API

All data processed throughout these scripts is stored in the `data/` directory.

## RQ1: Life Cycle of Vulnerabilities

RQ1 investigates the lifecycle of vulnerabilities in our dataset. We run the following scripts in sequence to analyze the data extracted in RQ0:

Step 1: Calculate Unique CVE by Severity
* `python -m src.data_analysis.rq0.table_1_unique_cve_by_severity`

Step 2: Calculate Mean Time to Mitigate
* `python -m src.data_analysis.rq1.table2_mean_time_to_mitigate`

## RQ2: Project Characteristics Correlation

RQ2 investigates the correlation between project characteristics and vulnerability life cycle. We extract repositories from Maven POM.xml files to find projects hosted on GitHub, and use OpenDigger to get repository metadata for GitHub-hosted repositories. We run the following scripts in sequence for data extraction:

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
* `python -m src.data_extraction.rq0.5_find_non_cve_artifacts`
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
* `python -m src.data_analysis.rq2.1_rank_biserial_bootstrap`

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
* `python -m src.data_analsysis.rq3.3_fig2_box_plot`