from typing import Any, Dict, List, Optional, Tuple
import requests
import time
import logging

from .config import MAVEN_POM_RETRIES, BACKOFF_FACTOR, BACKOFF_STARTING_TIME_IN_SECONDS

logging.basicConfig(level=logging.INFO)


def get_pom(
    group_id: str, artifact_id: str, version: str, retries: int = MAVEN_POM_RETRIES
) -> Optional[str]:
    """
    Constructs the POM URL and retrieves the POM file content with retries.
    """
    group_path = group_id.replace(".", "/")
    url = f"https://repo1.maven.org/maven2/{group_path}/{artifact_id}/{version}/{artifact_id}-{version}.pom"
    backoff = BACKOFF_STARTING_TIME_IN_SECONDS
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                logging.debug(
                    f"Successfully retrieved POM for {group_id}:{artifact_id}:{version}"
                )
                return response.text
            else:
                logging.warning(
                    f"Attempt {attempt}: Failed to retrieve POM for {group_id}:{artifact_id}:{version} "
                    f"- Status Code: {response.status_code}"
                )
        except requests.RequestException as e:
            logging.warning(
                f"Attempt {attempt}: Error fetching POM for {group_id}:{artifact_id}:{version} - {e}"
            )

        if attempt < retries:
            time.sleep(backoff)
            backoff *= BACKOFF_FACTOR
    logging.error(f"Exceeded maximum retries for {group_id}:{artifact_id}:{version}")
    return None


def get_pom_without_version(
    group_id: str, artifact_id: str, retries: int = MAVEN_POM_RETRIES
) -> Optional[str]:
    """
    Constructs the POM URL and retrieves the POM file content with retries.
    Does not require version - uses maven-metadata.xml to get latest version.
    """
    group_path = group_id.replace(".", "/")
    metadata_url = (
        f"https://repo1.maven.org/maven2/{group_path}/{artifact_id}/maven-metadata.xml"
    )
    backoff = BACKOFF_STARTING_TIME_IN_SECONDS

    # First try to get the maven metadata to find latest version
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(metadata_url, timeout=10)
            if response.status_code == 200:
                # Parse metadata to get latest version
                metadata = response.text
                import xml.etree.ElementTree as ET

                root = ET.fromstring(metadata)
                latest = root.find("versioning/latest")
                if latest is not None:
                    version = latest.text
                    # Now get the actual POM using the version
                    return get_pom(group_id, artifact_id, version, retries)
                else:
                    logging.warning(
                        f"No latest version found in metadata for {group_id}:{artifact_id}"
                    )
            else:
                logging.warning(
                    f"Attempt {attempt}: Failed to retrieve metadata for {group_id}:{artifact_id} "
                    f"- Status Code: {response.status_code}"
                )
        except requests.RequestException as e:
            logging.warning(
                f"Attempt {attempt}: Error fetching metadata for {group_id}:{artifact_id} - {e}"
            )
        except ET.ParseError as e:
            logging.warning(
                f"Attempt {attempt}: Error parsing metadata for {group_id}:{artifact_id} - {e}"
            )

        if attempt < retries:
            time.sleep(backoff)
            backoff *= BACKOFF_FACTOR

    logging.error(f"Exceeded maximum retries for {group_id}:{artifact_id}")
    return None
