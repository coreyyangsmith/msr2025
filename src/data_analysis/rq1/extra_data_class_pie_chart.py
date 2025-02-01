import pandas as pd
import matplotlib.pyplot as plt

# Replace 'data.csv' with your file path
file_path = "data/rq0_4_unique_cves_filtered.csv"

try:
    # Read the CSV file into a pandas DataFrame
    df = pd.read_csv(file_path)

    # Check if 'data_class' column exists
    if "data_class" not in df.columns:
        raise ValueError("The file does not contain a 'data_class' column.")

    # Filter out rows where data_class = -1
    df = df[df["data_class"] != -1]

    # Count the occurrences of each class
    class_counts = df["data_class"].value_counts().sort_index()

    # Define labels for the pie chart
    labels = ["Patch-Before-Publish", "Publish Only", "Publish-Before-Patch"]

    # Ensure that all classes (0,1,2) are represented, even if count is 0
    counts = [class_counts.get(i, 0) for i in range(3)]
    total = sum(counts)

    # Print the counts and percentages for each class
    for label, count in zip(labels, counts):
        percentage = (count / total) * 100
        print(f"{label}: {count} ({percentage:.2f}%)")

    # Define colors for each class (optional)
    colors = ["#ff9999", "#66b3ff", "#99ff99"]

    # Create the pie chart
    plt.figure(figsize=(8, 8))
    patches, texts, autotexts = plt.pie(
        counts,
        labels=labels,
        colors=colors,
        autopct="%1.1f%%",
        startangle=140,
        explode=(0.05, 0.05, 0.05),  # Slightly explode each slice
    )

    # Improve the text properties
    for text in texts:
        text.set_fontsize(12)
    for autotext in autotexts:
        autotext.set_fontsize(12)

    plt.title("Distribution of Data Classes", fontsize=16)
    plt.axis("equal")  # Equal aspect ratio ensures that pie is drawn as a circle.
    plt.tight_layout()
    plt.show()

except FileNotFoundError:
    print(f"Error: The file '{file_path}' was not found.")
except pd.errors.EmptyDataError:
    print("Error: The file is empty.")
except pd.errors.ParserError:
    print("Error: The file could not be parsed. Please check the file format.")
except ValueError as ve:
    print(f"Value Error: {ve}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
