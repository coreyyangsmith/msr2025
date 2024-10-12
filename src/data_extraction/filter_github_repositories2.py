import csv
import requests
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed


def get_pom(group_id, artifact_id, version):
    """
    Constructs the POM URL and retrieves the POM file content.
    """
    group_path = group_id.replace(".", "/")
    url = f"https://repo1.maven.org/maven2/{group_path}/{artifact_id}/{version}/{artifact_id}-{version}.pom"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.text
        else:
            print(
                f"Failed to retrieve POM for {group_id}:{artifact_id}:{version} - Status Code: {response.status_code}"
            )
            return None
    except requests.RequestException as e:
        print(f"Error fetching POM for {group_id}:{artifact_id}:{version} - {e}")
        return None


def get_github_url_from_pom(pom_xml):
    """
    Parses the POM XML to find the GitHub URL in the SCM section.
    """
    try:
        root = ET.fromstring(pom_xml)
        # Handle namespaces if present
        namespaces = {"m": root.tag.split("}")[0].strip("{")} if "}" in root.tag else {}
        scm = root.find("m:scm", namespaces) if namespaces else root.find("scm")
        if scm is not None:
            url_elem = scm.find("m:url", namespaces) if namespaces else scm.find("url")
            connection_elem = (
                scm.find("m:connection", namespaces)
                if namespaces
                else scm.find("connection")
            )
            if url_elem is not None and url_elem.text and "github.com" in url_elem.text:
                return url_elem.text.strip()
            if (
                connection_elem is not None
                and connection_elem.text
                and "github.com" in connection_elem.text
            ):
                return connection_elem.text.strip()
        return None
    except ET.ParseError:
        print("Error parsing POM XML.")
        return None


def parse_maven_artifact(artifact_string):
    # Split the artifact string by colon
    try:
        group_id, artifact_id = artifact_string.split(":")
        return {"group_id": group_id, "artifact_id": artifact_id}
    except ValueError:
        raise ValueError(
            "Artifact string is not in the correct format. Expected 'group_id:artifact_id'."
        )


def read_artifacts_from_csv(csv_file_path):
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
                    print(f"Missing fields in row: {row}")
    except FileNotFoundError:
        print(f"CSV file not found: {csv_file_path}")
    except Exception as e:
        print(f"Error reading CSV file: {e}")
    return artifacts


def process_artifact(artifact):
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
    # Path to your CSV file
    csv_file_path = "data/cve_lifetimes_updated.csv"  # Update this path as needed

    # Read artifacts from CSV
    artifacts = read_artifacts_from_csv(csv_file_path)
    if not artifacts:
        print("No artifacts to process.")
        return

    print(f"Total artifacts to process: {len(artifacts)}")

    github_artifacts = []
    non_github_artifacts = []

    # Use ThreadPoolExecutor for concurrent processing
    with ThreadPoolExecutor(max_workers=10) as executor:
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
                print(f"Error processing artifact {artifact}: {e}")

    # Output the results
    print("\nArtifacts hosted on GitHub:")
    print(len(github_artifacts))
    for art in github_artifacts:
        print(
            f"{art['groupId']}:{art['artifactId']}:{art['version']} - {art.get('githubUrl', '')}"
        )

    # Optionally, write the results to a new CSV file
    output_csv = "data/filtered_github_artifacts.csv"
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
        print(f"\nGitHub-hosted artifacts have been written to {output_csv}")
    except Exception as e:
        print(f"Error writing to output CSV: {e}")


if __name__ == "__main__":
    main()
