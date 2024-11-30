import pandas as pd
import matplotlib.pyplot as plt
import random
from datetime import datetime

# Read the CSV file
df = pd.read_csv("data/rq3_results_class_split.csv")

# Select a random row
random_row = df.iloc[random.randint(0, len(df) - 1)]

# Extract dates and convert to datetime with UTC timezone
dates = {
    "Affected Date": pd.to_datetime(random_row["affected_date"], utc=True),
    "CVE Publish Date": pd.to_datetime(random_row["cve_publish_date"], utc=True),
    "CVE Patch Date": pd.to_datetime(random_row["cve_patch_date"], utc=True),
    "Patched Date": pd.to_datetime(random_row["patched_date"], utc=True),
}

# Sort dates
sorted_dates = dict(sorted(dates.items(), key=lambda x: x[1]))

# Create figure and axis
fig, ax = plt.subplots(figsize=(12, 2))

# Plot timeline
y_pos = 0
for i, (event, date) in enumerate(sorted_dates.items()):
    ax.scatter(date, y_pos, s=100, zorder=2)
    ax.annotate(
        event,
        (date, y_pos),
        xytext=(0, 10),
        textcoords="offset points",
        ha="center",
        rotation=45,
    )

# Add connecting line
ax.plot(
    [min(dates.values()), max(dates.values())],
    [y_pos, y_pos],
    color="gray",
    linestyle="-",
    zorder=1,
)

# Format plot
ax.set_ylim(-0.5, 0.5)
ax.set_yticks([])
plt.title(
    f"Timeline for {random_row['dependent_artifact_id']} and {random_row['affected_parent_artifact_id']}\nCVE: {random_row['cve_id']}"
)

# Adjust layout to prevent label cutoff
plt.tight_layout()
plt.show()
