"""
This script cleans up POM dependency data files from previous runs.

It performs the following tasks:
1. Walks through all subdirectories in data/rq2_opendigger
2. Finds and deletes any pom_dependencies.csv files
3. Tracks number of files deleted and execution time

The script is used to clean up before re-running dependency extraction,
ensuring no stale data remains from previous runs.

Output:
- Prints status messages for each deleted file
- Reports total files deleted and execution time

Dependencies:
- os
- shutil
- time
"""

import os
import shutil
import time


def clear_pom_dependencies():
    """
    Delete all pom_dependencies.csv files from subdirectories in data/rq2_opendigger.

    Walks through the directory tree and removes any pom_dependencies.csv files found.
    Tracks and reports the number of files deleted and time taken.

    Returns:
        tuple: (files_found, elapsed_time)
            - files_found (int): Number of files that were deleted
            - elapsed_time (float): Time taken in seconds
    """
    base_dir = "data/rq2_opendigger"

    # Check if base directory exists
    if not os.path.exists(base_dir):
        print(f"Directory {base_dir} does not exist")
        return

    start_time = time.time()
    files_found = 0

    # Walk through all subdirectories
    for root, dirs, files in os.walk(base_dir):
        if "pom_dependencies.csv" in files:
            file_path = os.path.join(root, "pom_dependencies.csv")
            try:
                os.remove(file_path)
                files_found += 1
                print(f"Deleted {file_path}")
            except OSError as e:
                print(f"Error deleting {file_path}: {e}")

    elapsed_time = time.time() - start_time
    return files_found, elapsed_time


if __name__ == "__main__":
    print("Clearing pom_dependencies.csv files...")
    files_found, elapsed_time = clear_pom_dependencies()
    print(f"Done. Deleted {files_found} files in {elapsed_time:.2f} seconds")
