import csv
from typing import List, Dict, Tuple
import logging


def read_artifacts_from_csv(
    csv_file_path: str,
) -> Tuple[List[Dict[str, str]], List[str]]:
    """
    Reads artifacts from a CSV file and returns a list of dictionaries and fieldnames.
    """
    artifacts = []
    fieldnames = []
    try:
        with open(csv_file_path, mode="r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            fieldnames = reader.fieldnames if reader.fieldnames else []
            for row in reader:
                if (
                    "group_id" in row
                    and "artifact_id" in row
                    and "start_version" in row
                ):
                    artifacts.append(row)
                else:
                    logging.warning(f"Missing fields in row: {row}")
    except FileNotFoundError:
        logging.error(f"CSV file not found: {csv_file_path}")
    except Exception as e:
        logging.error(f"Error reading CSV file: {e}")
    return artifacts, fieldnames


def read_artifacts_from_csv_with_artifact(
    csv_file_path: str,
) -> Tuple[List[Dict[str, str]], List[str]]:
    """
    Reads artifacts from a CSV file that only contains 'artifact' column and returns a list of dictionaries and fieldnames.
    """
    artifacts = []
    fieldnames = []
    try:
        with open(csv_file_path, mode="r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            fieldnames = reader.fieldnames if reader.fieldnames else []
            for row in reader:
                if "artifact" in row:
                    artifacts.append(row)
                else:
                    logging.warning(f"Missing artifact field in row: {row}")
    except FileNotFoundError:
        logging.error(f"CSV file not found: {csv_file_path}")
    except Exception as e:
        logging.error(f"Error reading CSV file: {e}")
    return artifacts, fieldnames
