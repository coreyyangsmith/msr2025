import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns  # For better styling of KDE plots

# Read the data
df = pd.read_csv("data/rq3_results_class_split.csv")

# Convert dates to datetime with UTC timezone
date_columns = ["cve_publish_date", "cve_patch_date", "patched_date", "affected_date"]
for col in date_columns:
    df[col] = pd.to_datetime(df[col], utc=True)


# Classify each row based on date comparisons
def classify_row(row):
    if row["cve_publish_date"] < row["cve_patch_date"]:
        return "slow_patch"
    elif row["patched_date"] < row["cve_publish_date"]:
        return "fast_adoption"
    elif row["cve_publish_date"] > row["cve_patch_date"]:
        return "fast_patch"
    else:
        return "other_type"


df["data_class"] = df.apply(classify_row, axis=1)

# Calculate days between CVE publish date and patched date
df["days_to_patch"] = (
    df["patched_date"] - df["cve_publish_date"]
).dt.total_seconds() / (24 * 60 * 60)

# Export the enhanced dataset
df.to_csv("data/rq3_results_classified.csv", index=False)

# Define data classes and their corresponding colors (softened)
data_classes = ["fast_patch", "slow_patch", "fast_adoption"]
colors = ["#7fb5d9", "#8fc771", "#f5a94d"]  # Darker blue, green, orange

# Create figure and subplots
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# Add overall title
fig.suptitle(
    "Distribution of Days to Patch Across Different Classes",
    fontsize=16,
    fontweight="bold",
    y=1.05,
)

for ax, class_name, color in zip(axes, data_classes, colors):
    class_data = df[df["data_class"] == class_name]["days_to_patch"]

    # Plot histogram with softer edges
    sns.histplot(
        class_data,
        bins=30,
        color=color,
        kde=True,  # Enable KDE for trendline
        edgecolor="#cccccc",  # Lighter edge color
        ax=ax,
        alpha=0.75,  # Reduced opacity
    )

    # Add trendline with darker color and increased bandwidth for smoother curve
    sns.kdeplot(
        class_data,
        color="#000000",  # Changed to black for higher contrast
        linewidth=2,
        ax=ax,
        alpha=1,
        bw_adjust=1.5,  # Increase bandwidth for smoother curve
    )

    ax.set_xlabel("Days to Patch", fontsize=12)
    ax.set_ylabel("Frequency", fontsize=12)
    ax.set_title(class_name.replace("_", " ").title(), fontsize=14)

    # Set y-axis to start at 0
    ax.set_ylim(bottom=0)
    # Set x-axis bounds based on class
    if class_name == "fast_adoption":
        ax.set_xlim(right=0)
    else:
        ax.set_xlim(left=0)

    # Customize grid and spines with lighter colors
    ax.grid(True, linestyle="--", alpha=0.4)
    sns.despine(top=True, right=True, ax=ax)
    ax.spines["left"].set_color("#cccccc")
    ax.spines["bottom"].set_color("#cccccc")

# Adjust layout
plt.tight_layout()

# Save plot
plt.savefig(
    "data/rq3_patch_time_distribution_all_classes.png", dpi=300, bbox_inches="tight"
)

plt.show()
