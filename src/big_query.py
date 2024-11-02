from google.cloud import bigquery
import os

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "msr-2025-d058d9631c19.json"


def run_bigquery_query(query):
    # Initialize a BigQuery client
    client = bigquery.Client()

    # Execute the query
    query_job = client.query(query)

    # Wait for the job to complete
    results = query_job.result()

    # Process the results
    for row in results:
        print(row)


if __name__ == "__main__":
    # Define your SQL query
    sql_query = """
    SELECT 
    COUNT(*) AS total_fork_events
    FROM (
    SELECT * FROM `githubarchive.day.2014*` WHERE _TABLE_SUFFIX BETWEEN '0101' AND '1231'
    UNION ALL
    SELECT * FROM `githubarchive.day.2015*` WHERE _TABLE_SUFFIX BETWEEN '0101' AND '1231'
    UNION ALL
    SELECT * FROM `githubarchive.day.2016*` WHERE _TABLE_SUFFIX BETWEEN '0101' AND '1231'
    )
    WHERE 
    type = 'ForkEvent'
    AND repo.name = 'liferay/liferay-portal';
    """

    run_bigquery_query(sql_query)
