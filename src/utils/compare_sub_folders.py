import os
from typing import List, Set, Tuple


def compare_sub_folders(dir1: str, dir2: str) -> Tuple[Set[str], Set[str]]:
    """
    Compare the names of subfolders between two directories and find differences.

    Args:
        dir1: Path to first directory
        dir2: Path to second directory

    Returns:
        Tuple containing:
        - Set of folder names unique to dir1
        - Set of folder names unique to dir2
    """
    # Get list of subfolders in each directory
    folders1 = {
        name for name in os.listdir(dir1) if os.path.isdir(os.path.join(dir1, name))
    }
    folders2 = {
        name for name in os.listdir(dir2) if os.path.isdir(os.path.join(dir2, name))
    }

    # Find differences
    only_in_dir1 = folders1 - folders2
    only_in_dir2 = folders2 - folders1

    return only_in_dir1, only_in_dir2


# Compare folders between rq2_opendigger directories
only_in_rq2, only_in_o = compare_sub_folders(
    "data/rq2_opendigger", "data/o/rq2_opendigger/"
)

# Print results
print("\nFolders only in data/rq2_opendigger:")
for folder in sorted(only_in_rq2):
    print(f"- {folder}")

print("\nFolders only in data/o/rq2_opendigger/:")
for folder in sorted(only_in_o):
    print(f"- {folder}")
