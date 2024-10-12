import pandas as pd

path1 = "data/final_dataset.csv"

df = pd.read_csv(path1)

severity_mapping = {"UNKNOWN": 0, "LOW": 1, "MODERATE": 2, "HIGH": 3, "CRITICAL": 4}
df["severity_encoded"] = df["Severity"].map(severity_mapping)

df_filtered = df[df["stars"] != 0]
df_filtered = df_filtered.drop(
    columns=[
        "downloads",
        "dependencies",
        "build_status",
        "badges",
        "commit_frequency",
        "usage",
        "documentation",
        "test_code",
        "vulnerabilities",
    ]
)


df_filtered.to_csv("data/final_dataset_trimmed.csv")
