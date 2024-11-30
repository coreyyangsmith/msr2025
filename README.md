 // Start of Selection
# MSR 2025 - Dependency Mining Challenge

## Setup Instructions

1. **Install required dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

## Dataset
Our dataset is hosted on a Neo4j instance and contains 658,078 artifacts and X releases. It is downloaded and analyzed from OSV.dev on November 30th, 2024. For our initial data import, we use the `goblin_maven_2024_08_30.dump` dataset provided by the organizers. We run our queries using Neo4j version 4.4.36-community. We leverage Goblin Weaver API (v2.1.0) to extract additional information about the artifacts and releases, pertaining to CVEs, and use Goblin Weaver 

Our entire dataset and pipeline is hosted on Zenodo and can be found [here]().

## RQ0: Data Extraction and Processing
RQ0 contains our preliminary data processing and aims to extract high-level statistics and information about our dataset.

After setting up the project by adjusting the API links and number of workers, from the `src/utils/config.py` file, we can run the following scripts in sequence to extract our initial dataset:

`python -m src.data_extraction.rq0.1_extract_artifact_names_from_api`
Extract all artifact names from the API and save to `data/rq0_1_all_artifacts.csv`
Uses Neo4J Instance

`python -m src.data_extraction.rq0.2_enrich_artifact_data`
Enrich the artifact data with additional information pertaining to CVEsand save to `data/rq0_2_enriched_artifacts.csv`
Uses Neo4J Instance and Goblin Weaver API

`python -m src.data_extraction.rq0.3_extract_releases_cves`
Extract all releases and CVES for each release and save to `data/rq0_3_releases_with_cves.csv`
Uses Neo4J Instance and Goblin Weaver API

`python -m src.data_extraction.rq0.4_extract_unique_cves`
Extract all unique CVES and save to `data/rq0_4_unique_cves.csv`

All data processed throughout these scripts is stored in the `data/` directory.

## RQ1: Lifetime of Vulnerabilities