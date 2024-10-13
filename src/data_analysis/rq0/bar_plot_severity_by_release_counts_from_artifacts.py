import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Read the CSV file
df = pd.read_csv("data/artifacts_with_cves.csv")

# Sum up the counts for each severity level across all artifacts
low_count = df["low_severity_count"].sum()
medium_count = df["medium_severity_count"].sum()
high_count = df["high_severity_count"].sum()
critical_count = df["critical_severity_count"].sum()

# Prepare counts and severity levels
severity_levels = [
    "Low Severity",
    "Medium Severity",
    "High Severity",
    "Critical Severity",
]
counts = [low_count, medium_count, high_count, critical_count]

# Colors for each severity level
colors = ["#2ecc71", "#f1c40f", "#e67e22", "#e74c3c", "#95a5a6"]

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
