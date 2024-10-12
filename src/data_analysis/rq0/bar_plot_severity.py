import matplotlib.pyplot as plt
import numpy as np

# Data
severity_levels = [
    "Low Severity",
    "Medium Severity",
    "High Severity",
    "Critical Severity",
    "Unknown Severity",
]
# severity counts Low | Medium | High | Critical | Unknown

counts = [11090, 67870, 73390, 33717, 12]

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
        f"{height}",
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

plt.legend(loc="upper right", fontsize=6, frameon=False)
plt.savefig("figure.tiff", bbox_inches="tight", transparent=True, dpi=600)
plt.show()

# Adjust layout for better fit
plt.tight_layout()

# Show the plot
plt.show()
