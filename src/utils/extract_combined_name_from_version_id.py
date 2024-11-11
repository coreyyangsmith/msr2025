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
