from google.cloud import bigquery


def query_bigquery(project_id: str, dataset_id: str, query: str):
    """Extracts feedback records from BigQuery

    Args:
        project_id (str): BigQuery project ID
        dataset_id (str): BigQuery dataset ID
        query (str): SQL query to get data from BigQuery

    Returns:
        dict: Dictionary containing feedback records
    """
    # Initialize a BigQuery client
    client = bigquery.Client(project=project_id)

    # Construct a reference to the dataset
    # dataset_ref = client.dataset(dataset_id)

    # Make a BigQuery API request to run the query
    query_job = client.query(query)

    # Wait for the query to complete
    query_job.result()

    # Fetch the results of the query
    # results = query_job.result()

    # Write to dict
    result = [dict(row) for row in query_job]

    return result
