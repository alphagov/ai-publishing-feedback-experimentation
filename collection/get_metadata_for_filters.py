import os
import json
from src.utils.bigquery import query_bigquery

from src.sql_queries import (
    query_distinct_page_paths,
    query_distinct_orgs,
    query_distinct_doc_type,
)

from dotenv import load_dotenv

load_dotenv()

PUBLISHING_PROJECT_ID = os.getenv("PUBLISHING_PROJECT_ID")
PUBLISHING_VIEW = os.getenv("PUBLISHING_VIEW")
FILTER_OPTIONS_PATH = os.getenv("FILTER_OPTIONS_PATH")

queries = {
    "subject_page_path": query_distinct_page_paths,
    "organisation": query_distinct_orgs,
    "document_type": query_distinct_doc_type,
}

distinct_dimensions = {}
for dim, query in queries.items():
    print(f"Query for {dim} starting...")
    query = query.replace("@PUBLISHING_VIEW", str(PUBLISHING_VIEW))
    result = query_bigquery(
        project_id=PUBLISHING_PROJECT_ID, query=query, write_to_dict=False
    )
    distinct_dimensions[dim] = [row.values()[0] for row in result]
    print(f"Query for {dim} complete, with {len( distinct_dimensions[dim])} results.")

# Construct the full path
base_path = "app/"
path = os.path.join(base_path, FILTER_OPTIONS_PATH)

# Ensure the directory exists
os.makedirs(os.path.dirname(path), exist_ok=True)

# Create a json from distinct_dimensions
with open(path, "w") as f:
    json.dump(distinct_dimensions, f)

print(f"Filter options written to json at {path}")
