import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Set style for publication-quality plot
plt.style.use("seaborn-v0_8-paper")
plt.rcParams.update({"font.family": "Arial", "font.size": 12})

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
plt.figure(figsize=(4, 4))

# Create boxplot
sns.boxplot(
    data=df_filtered,
    x="Repository Update Strategy",
    y="Days to Patch",
    palette="Set2",
    width=0.5,
    showfliers=True,
)

# Customize plot
plt.title(
    "Time to Patch Distribution by\nRepository Update Strategy", fontsize=14, pad=15
)
plt.xlabel("Repository Update Strategy", fontsize=12)
plt.ylabel(
    "Days Between CVE Publication and Patch\n(Negative = Early Patch)", fontsize=12
)

# Add grid and adjust limits
plt.grid(axis="y", linestyle="--", alpha=0.3)
plt.ylim(-3000, 2000)

# Rotate x-axis labels for better fit
plt.xticks(rotation=15, fontsize=10)
plt.yticks(fontsize=10)

# Add statistics annotations
for i, strategy in enumerate(
    ["Slow Patch Adoption", "Fast Patch Adoption", "Adopt before Publish"]
):
    data = df_filtered[df_filtered["Repository Update Strategy"] == strategy][
        "Days to Patch"
    ]
    median = data.median()
    q1, q3 = data.quantile([0.25, 0.75])


plt.tight_layout()
plt.savefig("data/rq3_time_to_patch_boxplot.png", dpi=300, bbox_inches="tight")
plt.show()
