# Example usage
import pandas as pd

input_file = "data/artifacts_with_cves.csv"
output_file = "data/artifacts_with_cves_names_only.csv"


def extract_artifact_column(input_csv: str, output_csv: str) -> None:
    """
    Reads a CSV file, isolates the 'Artifact' column, and writes it to a new CSV file.

    Parameters:
    - input_csv (str): Path to the input CSV file.
    - output_csv (str): Path where the output CSV with only the 'Artifact' column will be saved.

    Raises:
    - FileNotFoundError: If the input CSV file does not exist.
    - ValueError: If the 'Artifact' column is not found in the input CSV.
    """
    try:
        # Read the input CSV file
        df = pd.read_csv(input_csv)
    except FileNotFoundError:
        raise FileNotFoundError(f"The file {input_csv} does not exist.")
    except pd.errors.EmptyDataError:
        raise ValueError("The input CSV file is empty.")
    except pd.errors.ParserError as e:
        raise ValueError(f"Error parsing the CSV file: {e}")

    # Check if 'Artifact' column exists
    if "artifact" not in df.columns:
        raise ValueError("The 'Artifact' column was not found in the input CSV.")

    # Isolate the 'Artifact' column
    df_artifact = df[["artifact"]]

    # Save the 'Artifact' column to the output CSV
    df_artifact.to_csv(output_csv, index=False)
    print(f"'Artifact' column has been successfully saved to {output_csv}")


extract_artifact_column(input_file, output_file)
