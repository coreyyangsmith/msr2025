import requests


def check_cve_for_release(package_name, ecosystem, version, cve_id):
    url = "https://api.osv.dev/v1/query"

    payload = {
        "version": version,
        "package": {"name": package_name, "ecosystem": ecosystem},
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return
    print(data)
    # Check if the CVE ID is in the results
    vulns = data.get("vulns", [])
    if not vulns:
        print(f"No vulnerabilities found for {package_name} version {version}.")
        return

    for vuln in vulns:
        if cve_id in vuln.get("aliases", []):
            print(
                f"The package {package_name} version {version} is affected by {cve_id}."
            )
            return

    print(f"The package {package_name} version {version} is NOT affected by {cve_id}.")


if __name__ == "__main__":
    # Example values for a Maven package
    package_name = "org.apache.logging.log4j:log4j-core"
    ecosystem = "Maven"
    version = "2.14.1"  # Version known to be affected
    cve_id = "CVE-2021-44228"

    check_cve_for_release(package_name, ecosystem, version, cve_id)
