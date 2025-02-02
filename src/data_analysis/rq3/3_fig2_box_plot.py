import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Set style for publication-quality plot
plt.style.use("seaborn-v0_8-paper")
sns.set_palette("colorblind")

# Read and prepare data
df = pd.read_csv("data/rq3_results_class_split.csv")

# Convert dates to datetime
date_columns = ["cve_publish_date", "cve_patch_date", "patched_date", "affected_date"]
for col in date_columns:
    df[col] = pd.to_datetime(df[col], utc=True)


# Classify update strategies
def classify_row(row):
    if (
        row["cve_publish_date"] <= row["cve_patch_date"]
        and row["cve_patch_date"] <= row["patched_date"]
    ):
        return "Slow Patch Adoption"
    elif (
        row["cve_patch_date"] <= row["cve_publish_date"]
        and row["cve_publish_date"] <= row["patched_date"]
    ):
        return "Fast Patch Adoption"
    elif (
        row["cve_patch_date"] <= row["patched_date"]
        and row["patched_date"] <= row["cve_publish_date"]
    ):
        return "Adopt before Publish"
    else:
        return "Other"


df["Repository Update Strategy"] = df.apply(classify_row, axis=1)
df["Days to Patch"] = (df["patched_date"] - df["cve_publish_date"]).dt.days

# Filter relevant classes
df_filtered = df[
    df["Repository Update Strategy"].isin(
        ["Slow Patch Adoption", "Fast Patch Adoption", "Adopt before Publish"]
    )
]

# Create figure
plt.figure(figsize=(8, 5))

# Create boxplot
bp = plt.boxplot(
    [
        df_filtered[df_filtered["Repository Update Strategy"] == strategy][
            "Days to Patch"
        ]
        for strategy in [
            "Slow Patch Adoption",
            "Fast Patch Adoption",
            "Adopt before Publish",
        ]
    ],
    labels=["Slow Patch Adoption", "Fast Patch Adoption", "Adopt before Publish"],
    patch_artist=True,
    flierprops={
        "marker": "o",
        "markerfacecolor": "#2C3E50",
        "markeredgecolor": "#2C3E50",
        "alpha": 0.4,
        "markersize": 4,
    },
    boxprops={
        "facecolor": "#3498db",
        "alpha": 0.7,
        "edgecolor": "#2C3E50",
        "linewidth": 1.5,
    },
    medianprops={"color": "#2C3E50", "linewidth": 2},
    whiskerprops={"color": "#2C3E50", "linewidth": 1.5},
    capprops={"color": "#2C3E50", "linewidth": 1.5},
)

# Add mean points and collect for legend
mean_points = []
for i, strategy in enumerate(
    ["Slow Patch Adoption", "Fast Patch Adoption", "Adopt before Publish"]
):
    data = df_filtered[df_filtered["Repository Update Strategy"] == strategy][
        "Days to Patch"
    ]
    mean = data.mean()
    mean_point = plt.plot(
        i + 1, mean, marker="D", color="#e74c3c", markersize=8, alpha=0.9
    )[0]
    mean_points.append(mean_point)

plt.xlabel("Repository Update Strategy", fontsize=14, labelpad=5, fontweight="bold")
plt.ylabel(
    "Days Between CVE Publication and Patch\n(Negative = Early Patch)",
    fontsize=14,
    fontweight="bold",
)

plt.grid(True, axis="y", linestyle="--", alpha=0.4)
plt.grid(False, axis="x")

plt.xticks(
    range(1, 4),
    ["Reactive \nAdoption", "Available Patch \nAdoption", "Proactive \nAdoption"],
    fontsize=14,
    fontweight="bold",
)
plt.yticks(fontsize=14, fontweight="bold")

# Add zero line
plt.axhline(y=0, color="#7f8c8d", linestyle="-", linewidth=1.2, alpha=0.6)

# Set y-axis minimum to -300
plt.ylim(bottom=-3000)
plt.ylim(top=2000)

# Add legend
legend_elements = [
    mean_points[0],
]
plt.legend(
    legend_elements,
    ["Mean"],
    loc="upper right",
    fontsize=12,
)

plt.tight_layout()
plt.savefig(
    "data/rq3_time_to_patch_boxplot.png",
    dpi=600,
    bbox_inches="tight",
    format="pdf",
)
plt.show()
