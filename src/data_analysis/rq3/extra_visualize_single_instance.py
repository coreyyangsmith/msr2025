import pandas as pd
import matplotlib.pyplot as plt
import random
from datetime import datetime

# Read the CSV file
df = pd.read_csv("data/rq3_results_class_split.csv")

cve_id = "CVE-2020-13953"
dependent_artifact = "org.apache.tapestry:tapestry-kaptcha"

# Allow selecting specific row by CVE ID and dependent artifact, otherwise random
if cve_id is not None and dependent_artifact is not None:
    print(
        f"Selected row for CVE: {cve_id} and dependent artifact: {dependent_artifact}"
    )
    selected_row = df[
        (df["cve_id"] == cve_id) & (df["dependent_artifact_id"] == dependent_artifact)
    ].iloc[0]
    print(selected_row)
else:
    selected_row = df.iloc[random.randint(0, len(df) - 1)]

# Extract dates and convert to datetime with UTC timezone
dates = {
    "Affected Date": pd.to_datetime(selected_row["affected_date"], utc=True),
    "CVE Publish Date": pd.to_datetime(selected_row["cve_publish_date"], utc=True),
    "CVE Patch Date": pd.to_datetime(selected_row["cve_patch_date"], utc=True),
    "Patched Date": pd.to_datetime(selected_row["patched_date"], utc=True),
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
    f"Timeline for {selected_row['dependent_artifact_id']} and {selected_row['affected_parent_artifact_id']}\nCVE: {selected_row['cve_id']}"
)

# Adjust layout to prevent label cutoff
plt.tight_layout()
plt.show()
