# Import necessary libraries
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Optional: Configure visualization aesthetics
sns.set(style="whitegrid", palette="muted", color_codes=True)


def load_data(file_path):
    """
    Load data from a CSV file into a pandas DataFrame.

    Parameters:
    - file_path (str): The path to the CSV file.

    Returns:
    - df (DataFrame): The loaded DataFrame.
    """
    try:
        df = pd.read_csv(file_path)
        print(f"Data successfully loaded from {file_path}")
        return df
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
        return None
    except pd.errors.EmptyDataError:
        print("Error: The file is empty.")
        return None
    except pd.errors.ParserError:
        print("Error: Could not parse the file.")
        return None


def explore_data(df):
    """
    Perform basic data exploration.

    Parameters:
    - df (DataFrame): The DataFrame to explore.
    """
    print("\nFirst 5 rows of the dataset:")
    print(df.head())

    print("\nDataset Information:")
    print(df.info())

    print("\nStatistical Summary:")
    print(df.describe())


def preprocess_data(df, metrics):
    """
    Preprocess the data by handling missing values and selecting relevant metrics.

    Parameters:
    - df (DataFrame): The DataFrame to preprocess.
    - metrics (list): List of column names to analyze.

    Returns:
    - df_clean (DataFrame): The preprocessed DataFrame.
    """
    # Check if all specified metrics exist in the DataFrame
    for metric in metrics:
        if metric not in df.columns:
            print(f"Warning: '{metric}' does not exist in the DataFrame.")

    # Select the relevant metrics
    df_selected = df[metrics]

    # Handle missing values by dropping rows with any missing values in selected metrics
    df_clean = df_selected.dropna()

    print(
        f"\nData after preprocessing: {df_clean.shape[0]} rows and {df_clean.shape[1]} columns."
    )
    return df_clean


def analyze_correlation(df, metrics, target_metric=None):
    """
    Analyze and visualize the correlation between specified metrics.

    Parameters:
    - df (DataFrame): The DataFrame containing the data.
    - metrics (list): List of column names to analyze.
    - target_metric (str, optional): If provided, only the correlations
      with this metric will be visualized.
    """
    # Calculate the correlation matrix
    corr_matrix = df[metrics].corr()
    print("\nCorrelation Matrix:")
    print(corr_matrix)

    # Determine what to plot
    if target_metric:
        if target_metric not in corr_matrix.columns:
            raise ValueError(f"'{target_metric}' is not in the list of metrics.")

        # Extract the target column
        single_corr = corr_matrix[[target_metric]].sort_values(
            by=target_metric, ascending=False
        )
        # Optionally, you can transpose for better visualization
        single_corr = single_corr.transpose()

        # Set up the matplotlib figure
        plt.figure(figsize=(8, 2))  # Adjust the size as needed

        # Generate a custom diverging colormap
        cmap = sns.diverging_palette(220, 10, as_cmap=True)

        # Draw the heatmap
        sns.heatmap(
            single_corr, annot=True, cmap=cmap, fmt=".2f", linewidths=0.5, cbar=True
        )

        plt.title(f"Correlation with '{target_metric}'")
    else:
        # Set up the matplotlib figure
        plt.figure(figsize=(10, 8))

        # Generate a custom diverging colormap
        cmap = sns.diverging_palette(220, 10, as_cmap=True)

        # Draw the heatmap with the mask and correct aspect ratio
        sns.heatmap(corr_matrix, annot=True, cmap=cmap, fmt=".2f", linewidths=0.5)

        plt.title("Correlation Matrix Heatmap")

    plt.tight_layout()
    plt.show()


def main():
    # Specify the path to your CSV file
    file_path = "data/final_dataset_trimmed.csv"  # Replace with your actual file path

    # Load the data
    df = load_data(file_path)
    if df is None:
        return  # Exit if data couldn't be loaded

    # Explore the data
    explore_data(df)

    # Specify the metrics/columns you want to analyze for correlation
    metrics = [
        "severity_encoded",
        "stars",
        "forks",
        "open_issues",
        "contributors",
        "watchers",
        "releases",
        "closed_issues",
    ]  # Replace with your actual column names

    # Preprocess the data
    df_clean = preprocess_data(df, metrics)

    # Analyze and visualize correlation
    analyze_correlation(df_clean, metrics, target_metric="severity_encoded")


if __name__ == "__main__":
    main()
