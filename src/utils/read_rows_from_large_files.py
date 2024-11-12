import csv


def count_rows_in_file(file_path):
    """Count the number of rows in a CSV file."""
    with open(file_path, mode="r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        row_count = sum(1 for row in reader)
    return row_count


file_path = "data/rq3_1_dependent_artifacts.csv"
row_count = count_rows_in_file(file_path)
print(f"Number of rows in '{file_path}': {row_count}")
