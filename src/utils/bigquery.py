from google.cloud import bigquery
from google.api_core.exceptions import NotFound


def query_bigquery(project_id: str, query: str, write_to_dict: bool = True):
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
    if write_to_dict:
        result = [dict(row) for row in query_job]
    else:
        result = query_job.result()

    return result


def write_to_bigquery(
    table_id: str,
    responses: list[dict],
    publishing_project_id: str,
) -> None:
    """
    Writes data to BigQuery
    """
    # Initialize a BigQuery client
    client = bigquery.Client(project=publishing_project_id)

    # Define schema for the table
    schema = [
        bigquery.SchemaField("id", "STRING"),
        bigquery.SchemaField("labels", "STRING", mode="REPEATED"),
        bigquery.SchemaField("urgency", "INTEGER"),
    ]

    # Create a list to hold the rows
    rows = []

    # Convert each response dictionary to a BigQuery row
    for response in responses:
        row = {
            "id": eval(response["open_labelled_records"])["id"],
            "labels": eval(response["open_labelled_records"])["labels"],
            "urgency": eval(response["open_labelled_records"])["urgency"],
        }
        rows.append(row)

    # Write rows to BigQuery
    try:
        table = client.get_table(table_id)
    except NotFound:
        table = bigquery.Table(table_id, schema=schema)
        table = client.create_table(table)

    errors = client.insert_rows(table, rows)
    if errors == []:
        print(f"Data inserted into table {table_id}")
    else:
        print(f"Errors occurred while inserting data into table {table_id}: {errors}")
