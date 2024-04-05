import os
from dotenv import load_dotenv
import argparse

from qdrant_client.http.models import Distance

from src.collection.set_collection import (
    create_collection,
    create_vectors_from_data,
    upsert_to_collection_from_vectors,
    get_latest_snapshot_location,
)
from src.sql_queries import query_labelled_feedback, query_all_feedback
from src.utils.bigquery import query_bigquery
from src.utils.utils import load_qdrant_client

load_dotenv()
PUBLISHING_PROJECT_ID = os.getenv("PUBLISHING_PROJECT_ID")
LABELLED_FEEDBACK_TABLE = os.getenv("EVALUATION_TABLE")
PUBLISHING_VIEW = os.getenv("PUBLISHING_VIEW")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
EVAL_COLLECTION_NAME = os.getenv("EVAL_COLLECTION_NAME")
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_PORT = os.getenv("QDRANT_PORT")

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

if args.eval_only:
    collections = [(EVAL_COLLECTION_NAME, eval_query_read)]
    print("Running for evaluation collection only")
else:
    collections = [
        (COLLECTION_NAME, all_query_read),
        (EVAL_COLLECTION_NAME, eval_query_read),
    ]

snapshots = []
# Create feedback and eval collections
for name, query in collections:
    print(f"Running for collection {name}...")
    # Check if snapshot exists on disk, populate from that if arg
    try:
        # If snapshots are available, and we want to use them to restore, list them
        if args.restore_from_snapshot:
            snapshots = client.list_snapshots(name)
            print(f"{len(snapshots)} snapshots found for collection {name}")

    except Exception as e:
        print(f"Snapshots not available: {e}")

    if snapshots and args.restore_from_snapshot:
        # If snapshots are available, and we want to use them to restore, restore from latest
        latest_snapshot = get_latest_snapshot_location(snapshots)

        print(f"Restoring collection {name} from snapshot {latest_snapshot}...")
        client.recover_snapshot(
            name,
            location=f"file:///qdrant/snapshots/{name}/{latest_snapshot}",
            wait=True,
        )

    else:
        # If either no snapshots available, or arg not set, populate from BigQuery
        print("Restore from snapshot not requested, or snapshots not present")

        print("Reading data from BigQuery...")
        docs = query_bigquery(
            PUBLISHING_PROJECT_ID,
            query,
        )

        print(f"Creating collection {name} with {len(docs)} documents...")
        create_collection(client, name, size=768, distance_metric=Distance.COSINE)

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
