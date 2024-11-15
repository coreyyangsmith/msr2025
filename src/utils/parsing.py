import xml.etree.ElementTree as ET
import re
from typing import Optional, Dict, Tuple
import logging
from urllib import parse


def get_scm_url_from_pom(pom_xml: str) -> Optional[str]:
    """
    Parses a Maven POM XML string to extract the SCM URL from the SCM section.

    Args:
        pom_xml (str): The raw XML content of a Maven POM file

    Returns:
        Optional[str]: The SCM URL if found in the POM file's SCM section, None if:
            - No SCM section exists
            - No URL is found in the SCM section
            - The XML cannot be parsed

    Example:
        >>> pom_content = '''
        ... <project>
        ...   <scm>
        ...     <url>https://github.com/owner/repo</url>
        ...   </scm>
        ... </project>
        ... '''
        >>> url = get_scm_url_from_pom(pom_content)
        >>> print(url)
        'https://github.com/owner/repo'
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
            scm_url = _extract_scm_url(scm, ns)
            return scm_url
        return None
    except ET.ParseError as e:
        logging.error(f"Error parsing POM XML: {e}")
        return None


def _extract_scm_url(scm_element: ET.Element, ns: Dict[str, str]) -> Optional[str]:
    """
    Extracts the SCM URL from the SCM element of a POM file.

    Args:
        scm_element (ET.Element): The SCM XML element to extract the URL from
        ns (Dict[str, str]): XML namespace mapping dictionary. If empty, no namespace is used.

    Returns:
        Optional[str]: The extracted SCM URL if found in any of the following tags (in order):
            - url
            - connection
            - developerConnection
            Returns None if no URL is found.

    Example:
        >>> scm = root.find(".//scm")
        >>> ns = {"ns": "http://maven.apache.org/POM/4.0.0"}
        >>> url = _extract_scm_url(scm, ns)
        >>> print(url)
        'https://github.com/owner/repo'
    """
    tags = ["url", "connection", "developerConnection"]
    for tag in tags:
        if ns:
            url_elem = scm_element.find(f"ns:{tag}", ns)
        else:
            url_elem = scm_element.find(tag)
        if url_elem is not None and url_elem.text:
            return url_elem.text.strip()
    return None


def extract_github_url(scm_url: str) -> Optional[str]:
    """
    Extracts and standardizes a GitHub URL from an SCM URL by converting various formats
    to a consistent HTTPS URL format.

    Args:
        scm_url (str): The SCM URL to extract from, which may be in various formats like:
            - https://github.com/owner/repo
            - git@github.com:owner/repo.git
            - scm:git:git@github.com:owner/repo.git
            - git://github.com/owner/repo

    Returns:
        Optional[str]: A standardized GitHub HTTPS URL in the format
            'https://github.com/owner/repo' if a valid GitHub repository is found,
            None otherwise.

    Example:
        >>> extract_github_url("git@github.com:apache/kafka.git")
        'https://github.com/apache/kafka'
        >>> extract_github_url("https://gitlab.com/owner/repo")
        None
    """
    # Pattern to match common GitHub URL structures and extract owner/repo
    pattern = re.compile(
        r"(?:github\.com[:/]|@github\.com[:/])([^/]+?)/([^/]+?)(?:\.git|/|$)"
    )
    match = pattern.search(scm_url)
    if match:
        owner, repo = match.groups()
        return f"https://github.com/{owner}/{repo}"
    else:
        logging.warning(f"Invalid GitHub URL structure in SCM URL: {scm_url}")
        return None


def extract_owner_repo_from_github_url(
    github_url: str,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Extracts the owner and repository name from a GitHub URL.

    This function parses a GitHub URL and extracts the owner (user/organization) and repository
    name components. It handles URLs in formats like:
    - https://github.com/owner/repo
    - https://github.com/owner/repo.git
    - www.github.com/owner/repo

    Args:
        github_url (str): The GitHub URL to parse. Should be a valid HTTPS GitHub URL.

    Returns:
        Tuple[Optional[str], Optional[str]]: A tuple containing:
            - owner (str): The GitHub user/organization name, or None if invalid
            - repo (str): The repository name without .git suffix, or None if invalid

    Example:
        >>> extract_owner_repo_from_github_url("https://github.com/apache/kafka")
        ('apache', 'kafka')
        >>> extract_owner_repo_from_github_url("https://gitlab.com/owner/repo")
        (None, None)
    """
    parsed_url = parse.urlparse(github_url)
    if parsed_url.netloc not in ["github.com", "www.github.com"]:
        logging.warning(f"Invalid GitHub URL: {github_url}")
        return None, None

    path_parts = parsed_url.path.strip("/").split("/")

    if len(path_parts) >= 2:
        owner = path_parts[0]
        repo = path_parts[1].replace(".git", "")
        return owner, repo
    else:
        logging.warning(f"Invalid GitHub URL structure: {github_url}")
        return None, None


def extract_combined_name_from_version_id(version_id: str) -> str:
    """
    Extracts the full artifact name (without version) from a version ID string.

    Args:
        version_id: String in format "group:artifact:version"

    Returns:
        String containing "group:artifact" portion

    Example:
        >>> extract_combined_name_from_version_id("app.cybrid:cybrid-api-bank-java:v0.51.4")
        'app.cybrid:cybrid-api-bank-java'
    """
    # Split on : and take everything except the last segment (version)
    parts = version_id.split(":")
    return ":".join(parts[:-1])
