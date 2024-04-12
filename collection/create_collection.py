import os
from dotenv import load_dotenv
import argparse

from qdrant_client.http.models import Distance

from src.collection_utils.set_collection import (
    create_collection,
    create_vectors_from_data,
    upsert_to_collection_from_vectors,
    restore_collection_from_snapshot,
)
from src.sql_queries import query_labelled_feedback, query_all_feedback
from src.utils.bigquery import query_bigquery
from src.utils.utils import load_qdrant_client


load_dotenv()

PUBLISHING_PROJECT_ID = os.getenv("PUBLISHING_PROJECT_ID")
LABELLED_FEEDBACK_TABLE = os.getenv("EVALUATION_TABLE")
PUBLISHING_VIEW = os.getenv("PUBLISHING_VIEW")
PUBLISHING_VIEW = f"`{PUBLISHING_VIEW}`"
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
EVAL_COLLECTION_NAME = os.getenv("EVAL_COLLECTION_NAME")
QDRANT_HOST = os.getenv("QDRANT_HOST_EXTERNAL")  # Use external IP address
QDRANT_PORT = os.getenv("QDRANT_PORT")

# Qdrant args
size = 768
distance_metric = Distance.COSINE

# TODO: Add logging
parser = argparse.ArgumentParser(description="Create a Qdrant collection from BigQuery")

# Add arg for populate from snapshot or from BigQuery
parser.add_argument(
    "-ev",
    "--eval-only",
    action="store_true",  # This will set the value to True when the flag is used
    default=False,  # Default value is False
    dest="eval_only",
    help="Set to True to populate only the evaluation collection. Defaults to False.",
)

# Add arg for populate from snapshot or from BigQuery
parser.add_argument(
    "-rs",
    "--restore-from-snapshot",
    action="store_true",  # This will set the value to True when the flag is used
    default=False,  # Default value is False
    dest="restore_from_snapshot",
    help="Set to True to enable restoring from a snapshot. Defaults to False.",
)

args = parser.parse_args()

client = load_qdrant_client(QDRANT_HOST, port=QDRANT_PORT)

all_query_read = query_all_feedback.replace("@PUBLISHING_VIEW", str(PUBLISHING_VIEW))
eval_query_read = query_labelled_feedback.replace(
    "@LABELLED_FEEDBACK_TABLE", str(LABELLED_FEEDBACK_TABLE)
).replace("@PUBLISHING_VIEW", str(PUBLISHING_VIEW))

# If eval_only, only populate the evaluation collection. Otherwise populate both
if args.eval_only:
    collections = [(EVAL_COLLECTION_NAME, eval_query_read)]
    print("Running for evaluation collection only")
else:
    collections = [
        (COLLECTION_NAME, all_query_read),
        (EVAL_COLLECTION_NAME, eval_query_read),
    ]

for name, query in collections:
    print(f"Running for collection {name}...")
    if args.restore_from_snapshot:
        print("Attempting to restore from snapshot...")
        operation = restore_collection_from_snapshot(
            client,
            name,
            size,
            distance_metric,
        )
        print(f"Restore from snapshot: {operation['success']}, {operation['message']}")
    if not all(
        [operation["success"], args.restore_from_snapshot]
    ):  # If either no snapshots available, or arg not set, populate from BigQuery
        print(
            "Creating collection from vectors: restore from snapshot not requested, or snapshots not present"
        )
        print("Reading data from BigQuery...")
        docs = query_bigquery(
            PUBLISHING_PROJECT_ID,
            query,
        )

        print(f"Creating collection {name} with {len(docs)} documents...")
        create_collection(client, name, size=size, distance_metric=distance_metric)

        # Convert data into PointStructs for upsertion
        points_to_upsert = create_vectors_from_data(
            docs, id_key="feedback_record_id", embedding_key="embeddings"
        )
        upsert_to_collection_from_vectors(client, name, data=points_to_upsert)
        print(
            f"Collection {name} created and upserted with {len(points_to_upsert)} points"
        )

        # Create snapshot on disk
        client.create_snapshot(collection_name=name, wait=True)

    print(f"Collection {name} ready!")
