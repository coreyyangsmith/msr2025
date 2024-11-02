import csv
import logging
import re
import requests
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import StringIO
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

"""
Parses POM XML to find matching GitHub URLs
"""


def get_pom(
    group_id: str, artifact_id: str, version: str, retries: int = 3
) -> Optional[str]:
    """
    Constructs the POM URL and retrieves the POM file content with retries.
    """
    group_path = group_id.replace(".", "/")
    url = f"https://repo1.maven.org/maven2/{group_path}/{artifact_id}/{version}/{artifact_id}-{version}.pom"
    backoff = 1  # Initial backoff delay in seconds
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                logging.debug(
                    f"Successfully retrieved POM for {group_id}:{artifact_id}:{version}"
                )
                return response.text
            else:
                print(url)
                logging.warning(
                    f"Attempt {attempt}: Failed to retrieve POM for {group_id}:{artifact_id}:{version} "
                    f"- Status Code: {response.status_code}"
                )
        except requests.RequestException as e:
            print(url)
            logging.warning(
                f"Attempt {attempt}: Error fetching POM for {group_id}:{artifact_id}:{version} - {e}"
            )

        if attempt < retries:
            time.sleep(backoff)
            backoff *= 2  # Exponential backoff
    logging.error(f"Exceeded maximum retries for {group_id}:{artifact_id}:{version}")
    return None


def get_github_url_from_pom(pom_xml: str) -> Optional[str]:
    """
    Parses the POM XML to find the GitHub URL in the SCM section.
    """
    try:
        root = ET.fromstring(pom_xml)

        # Extract the namespace, if any
        namespace_match = re.match(r"\{(.*)\}", root.tag)
        namespace = namespace_match.group(1) if namespace_match else ""
        ns = {"ns": namespace} if namespace else {}

        # Search for the SCM element
        scm = root.find(".//ns:scm", ns) if namespace else root.find(".//scm")
        if scm is not None:
            github_url = _extract_github_url_from_scm(scm, ns)
            if github_url:
                return github_url
        return None
    except ET.ParseError as e:
        print(pom_xml)
        logging.error(f"Error parsing POM XML: {e}")
        return None


def _extract_github_url_from_scm(
    scm_element: ET.Element, ns: Dict[str, str]
) -> Optional[str]:
    """
    Extracts GitHub URL from the SCM element.
    """
    tags = ["url", "connection", "developerConnection"]
    for tag in tags:
        if ns:
            url_elem = scm_element.find(f"ns:{tag}", ns)
        else:
            url_elem = scm_element.find(tag)
        if url_elem is not None and url_elem.text and "github.com" in url_elem.text:
            return url_elem.text.strip()
    return None


def parse_maven_artifact(artifact_string: str) -> Dict[str, str]:
    # Split the artifact string by colon
    try:
        group_id, artifact_id = artifact_string.split(":")
        return {"group_id": group_id, "artifact_id": artifact_id}
    except ValueError:
        raise ValueError(
            "Artifact string is not in the correct format. Expected 'group_id:artifact_id'."
        )


def read_artifacts_from_csv(csv_file_path: str) -> List[Dict[str, str]]:
    """
    Reads artifacts from a CSV file and returns a list of dictionaries.
    """
    artifacts = []
    try:
        with open(csv_file_path, mode="r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Ensure required fields are present
                if "Artifact" in row and "Start Version" in row:
                    info = parse_maven_artifact(row["Artifact"].strip())
                    artifacts.append(
                        {
                            "groupId": info["group_id"],
                            "artifactId": info["artifact_id"],
                            "version": row["Start Version"].strip(),
                        }
                    )
                else:
                    logging.warning(f"Missing fields in row: {row}")
    except FileNotFoundError:
        logging.error(f"CSV file not found: {csv_file_path}")
    except Exception as e:
        logging.error(f"Error reading CSV file: {e}")
    return artifacts


def process_artifact(artifact: Dict[str, str]) -> Dict[str, str]:
    """
    Processes a single artifact to determine if it's hosted on GitHub.
    Returns the artifact dictionary with an additional key 'hostedOnGitHub' and 'githubUrl' if applicable.
    """
    pom = get_pom(artifact["groupId"], artifact["artifactId"], artifact["version"])
    if pom:
        github_url = get_github_url_from_pom(pom)
        if github_url:
            artifact["hostedOnGitHub"] = True
            artifact["githubUrl"] = github_url
        else:
            artifact["hostedOnGitHub"] = False
    else:
        artifact["hostedOnGitHub"] = False
    return artifact


def main():
    input_path = (
        "data/rq1_cve_lifetimes_updated_trimmed.csv"  # Update this path as needed
    )
    output_csv = "data/rq2_filtered_github_artifacts.csv"

    artifacts = read_artifacts_from_csv(input_path)
    if not artifacts:
        logging.info("No artifacts to process.")
        return

    logging.info(f"Total artifacts to process: {len(artifacts)}")

    github_artifacts = []
    non_github_artifacts = []

    # Use ThreadPoolExecutor for concurrent processing
    max_workers = min(
        10, len(artifacts)
    )  # Adjust number of workers based on artifact count
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_artifact = {
            executor.submit(process_artifact, artifact): artifact
            for artifact in artifacts
        }
        for future in as_completed(future_to_artifact):
            artifact = future_to_artifact[future]
            try:
                result = future.result()
                if result.get("hostedOnGitHub"):
                    github_artifacts.append(result)
                else:
                    non_github_artifacts.append(result)
            except Exception as e:
                logging.error(f"Error processing artifact {artifact}: {e}")

    # Output the results
    logging.info(f"Artifacts hosted on GitHub: {len(github_artifacts)}")
    for art in github_artifacts:
        logging.debug(
            f"{art['groupId']}:{art['artifactId']}:{art['version']} - {art.get('githubUrl', '')}"
        )

    try:
        with open(output_csv, mode="w", newline="", encoding="utf-8") as csvfile:
            fieldnames = ["groupId", "artifactId", "version", "githubUrl"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for art in github_artifacts:
                writer.writerow(
                    {
                        "groupId": art["groupId"],
                        "artifactId": art["artifactId"],
                        "version": art["version"],
                        "githubUrl": art.get("githubUrl", ""),
                    }
                )
        logging.info(f"GitHub-hosted artifacts have been written to {output_csv}")
    except Exception as e:
        logging.error(f"Error writing to output CSV: {e}")


if __name__ == "__main__":
    main()
