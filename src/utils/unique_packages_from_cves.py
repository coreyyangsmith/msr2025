import csv


def get_unique_github_repos(file_path: str) -> int:
    """
    Reads the specified CSV file and returns the unique count of {github_owner}/{github_repo}.
    """
    unique_repos = set()

    try:
        with open(file_path, "r") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                github_owner = row["github_owner"]
                github_repo = row["github_repo"]
                unique_repos.add(f"{github_owner}/{github_repo}")
    except Exception as e:
        print(f"Failed to read file {file_path}: {e}")

    return len(unique_repos)


print(get_unique_github_repos("data/rq2_1_github_repositories_by_cve_filtered.csv"))
