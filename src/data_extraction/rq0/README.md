# RQ0 - Quantify Vulnerabilities in Maven

Considering the [MSR 2025 Mining Challenge](https://2025.msrconf.org/track/msr-2025-mining-challenge), we leverage the provided Goblin Dataset dated [August 30th 2024](https://zenodo.org/records/13734581) available on Zenodo Archive. We use the `with_metrics_goblin_maven_30_08_24.dump` file to avoid any discrepancies in the data collection process.

Our first step is to examine characiteristics of this base dataset, before moving forward with additional processing and analysis.

| Dataset | Dataset Date | Total Artifacts   | Total Releases | Total Latest Releases | Total Dependencies | Artifacts w/ 1+ CVE | Release w/ 1+ CVE | Latest Rel w/ 1+ CVE |
| ------- | ------------ | ----------------- | -------------- | --------------------- | ------------------ | ------------------- | ----------------- | -------------------- |
| Ours    | 2024-08-30   | 620,472 (625,472) | 13,452,510     | to be found           | to be found        | 1,433               | 81,321 (0.605%)   | to be found          |

### 1. Dataset Statistics
First, we leverage 'Neo4J Docker Verion 4.4.36-community' to obtain some high-level information about the provided dataset. We examine the total number of releases and artifacts, the number of latest releases, and the total number of dependencies.

To do this, we run the following Cypher queries within Neo4J Desktop to obtain the information.

#### Total Artifacts
`MATCH (a:Artifact)
RETURN COUNT(a) AS artifactCount;`

#### Total Releases
`MATCH (r:Release)
RETURN COUNT(r) AS releaseCount;`

#### Total Latest Releases
`MATCH (a:Artifact)-[:relationship_AR]->(r:Release)
WITH a, r
ORDER BY r.timestamp DESC
WITH a, COLLECT(r)[0] AS latestRelease
RETURN COUNT(latestRelease) AS latestReleaseCount;`

#### Total Dependencies
`MATCH (:Release)-[r:dependency]->(:Artifact)
RETURN COUNT(r) AS dependencyCount;`

### 2. Severity Information
In order to perform a detailed analysis on the lifetimes of vulnerabilities, and observe how other metrics may correlate with the outcomes of projects, we must extract the relevant releases and artifacts that contain CVEs. To do so, we process through the entire dataset.

#### Artifacts with at least one CVE
Since there are many times more releases than artifacts, we first extract a list of all artifacts from the Maven Repository using `coding_file_here.py`

After having this comprehensive list of Artifacts within the Maven Central Repository ecosystem, we process through all artifacts and extract ones which contain at least one release with a CVE. We import our `artifacts.csv` intermediary dataset, and process through `coding_file_here.py` to extract `artifacts_with_cves.csv`

#### Releases with at least one CVE
Now having a reduced search space, we re-process just the artifacts_with_cves.csv and extract a list of `releases_with_cves.csv` using `coding_file_here.py`

#### Latest Releases with at least one CVE
After having a list of `releases_with_cves.csv`, we compare the information extracted from the previous process with our `latest_releases.csv` obtained in step 1, and extract for matching pairs of latest releases CVEs that contain CVE information.

### 3. Results
From this information, we can plot the distribution of CVE severity across releases both visually, and within a table. All chart generation code is dependent on generated csv's obtained from running data_extraction methods. All code related to the generation of figures can be found in `src/data_analysis`