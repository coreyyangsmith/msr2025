import os
import csv

from ...utils.config import RQ2_3_OUTPUT

# Path to the opendigger data directory
opendigger_dir = "data/rq2_opendigger"

# Get all folder names in the directory
folder_names = [
    name
    for name in os.listdir(opendigger_dir)
    if os.path.isdir(os.path.join(opendigger_dir, name))
]

# Convert folder names back to repository format (replace _ with /)
repo_names = [folder_name.replace("_", "/", 1) for folder_name in folder_names]

# Write to CSV
output_file = RQ2_3_OUTPUT
with open(output_file, "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    for repo in repo_names:
        writer.writerow([repo])

print(f"Found {len(repo_names)} repositories")
print(f"Repository names written to {output_file}")
