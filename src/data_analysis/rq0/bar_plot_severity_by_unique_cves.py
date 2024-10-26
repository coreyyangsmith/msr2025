import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Read the CSV file
df = pd.read_csv("data/rq1_cve_lifetimes.csv")

# Mapping of severities from CSV to severity_levels labels
severity_mapping = {
    "LOW": "Low Severity",
    "MODERATE": "Moderate Severity",
    "HIGH": "High Severity",
    "CRITICAL": "Critical Severity",
}

# Map the severity column to match the labels used in the plot
df["Severity_Mapped"] = df["Severity"].map(severity_mapping)

# Define the severity levels in the desired order
severity_levels = [
    "Low Severity",
    "Moderate Severity",
    "High Severity",
    "Critical Severity",
]

# Count the number of incidents for each severity level
severity_counts = df["Severity_Mapped"].value_counts()

# Ensure counts are in the same order as severity_levels
counts = [severity_counts.get(sev, 0) for sev in severity_levels]

# Colors for each severity level
colors = ["#2ecc71", "#f1c40f", "#e67e22", "#e74c3c"]

# Create a figure and axis
fig, ax = plt.subplots(figsize=(10, 6))

# Create bar chart
bars = ax.bar(severity_levels, counts, color=colors, edgecolor="black")

# Add counts on top of each bar
for bar in bars:
    height = bar.get_height()
    ax.annotate(
        f"{int(height)}",
        xy=(bar.get_x() + bar.get_width() / 2, height),
        xytext=(0, 5),  # 5 points vertical offset
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=10,
        fontweight="bold",
    )

# Set title and labels
ax.set_title("Incident Counts by Severity Level", fontsize=16, fontweight="bold")
ax.set_xlabel("Severity Level", labelpad=0)
ax.set_ylabel("Number of Incidents", labelpad=-1)

# Add grid for y-axis
ax.yaxis.grid(True, linestyle="--", which="major", color="grey", alpha=0.5)

# Adjust layout for better fit
plt.tight_layout()

# Save and show the plot
plt.savefig("figure.tiff", bbox_inches="tight", transparent=True, dpi=600)
plt.show()
