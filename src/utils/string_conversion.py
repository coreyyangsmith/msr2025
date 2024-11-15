import logging
from urllib import parse


def convert_github_url_to_api(github_url):
    """
    Convert a standard GitHub URL to its corresponding GitHub API URL.

    Args:
        github_url (str): The GitHub URL to convert.

    Returns:
        str or None: The corresponding GitHub API URL, or None if the input URL is invalid.
    """
    # Parse the URL
    parsed_url = parse.urlparse(github_url)

    # Ensure the URL is from github.com
    if parsed_url.netloc not in ["github.com", "www.github.com"]:
        logging.warning(f"Invalid GitHub URL: {github_url}")
        return None

    # Split the path and remove any trailing slash
    path = parsed_url.path.rstrip("/")

    # Remove .git suffix if present
    if path.endswith(".git"):
        path = path[:-4]

    # Split the path into components
    path_parts = path.strip("/").split("/")

    # The first two parts should be the owner and repo
    if len(path_parts) >= 2:
        owner = path_parts[0]
        repo = path_parts[1]
        # Initialize the base API URL
        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        return api_url
    else:
        logging.warning(f"Invalid GitHub URL structure: {github_url}")
        return None
