import pandas as pd

df = pd.DataFrame(
    {
        "parent_combined_name": [
            "LOGGER.JAVA",
            "LOGGER.JAVA",
            "Database.java",
            "Database.java",
        ],
        "dependent_combined_name": [
            "FileUtils.java",
            "FileUtils.java",
            "FileUtils.java",
            "Connection.java",
        ],
    }
)
df = df.drop_duplicates(subset=["parent_combined_name", "dependent_combined_name"])
print(df)
