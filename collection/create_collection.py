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
from src.utils.utils import load_qdrant_client, load_config

load_dotenv()
PUBLISHING_PROJECT_ID = os.getenv("PUBLISHING_PROJECT_ID")
LABELLED_FEEDBACK_TABLE = os.getenv("EVALUATION_TABLE")
PUBLISHING_VIEW = os.getenv("PUBLISHING_VIEW")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
EVAL_COLLECTION_NAME = os.getenv("EVAL_COLLECTION_NAME")
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_PORT = os.getenv("QDRANT_PORT")

config = load_config(".config/config.json")

# TODO: add arg parser for populate from snapshot or not
parser = argparse.ArgumentParser(description="Create a Qdrant collection from BigQuery")

# Add a boolean argument that defaults to True.
# Use 'store_false' to set the value to False when the flag is present.
parser.add_argument(
    "-rs",
    "--restore-from-snapshot",
    action="store_true",  # This will set the value to False when the flag is used
    default=False,  # Default value is False
    dest="restore_from_snapshot",
    help="Set to True to disable restoring from a snapshot. Defaults to False.",
)

args = parser.parse_args()

client = load_qdrant_client(QDRANT_HOST, port=QDRANT_PORT)

all_query_read = query_all_feedback.replace("@PUBLISHING_VIEW", str(PUBLISHING_VIEW))

eval_query_read = query_labelled_feedback.replace(
    "@LABELLED_FEEDBACK_TABLE", str(LABELLED_FEEDBACK_TABLE)
).replace("@PUBLISHING_VIEW", str(PUBLISHING_VIEW))

# Create feedback and eval collections
for name, query in [
    # (COLLECTION_NAME, all_query_read),
    (EVAL_COLLECTION_NAME, eval_query_read)
]:
    if args.restore_from_snapshot:
        # Check if snapshot exists on disk, populate from that if arg
        try:
            snapshots = client.list_snapshots(name)
            print(f"{len(snapshots)} snapshots found for collection {name}")

            latest_snapshot = get_latest_snapshot_location(snapshots)
            print(f"latest snapshot: {latest_snapshot}")

            print(f"Restoring collection {name} from snapshot {latest_snapshot}...")
            client.recover_snapshot(
                name,
                location=f"file:///qdrant/snapshots/{name}/{latest_snapshot}",
                wait=True,
            )

            # Clean up old snapshots
            for snapshot in snapshots:
                if snapshot.name != latest_snapshot:
                    print(f"Deleting snapshot {snapshot.name}...")
                    client.delete_snapshot(name, snapshot.name)
        except Exception as e:
            print(f"Error finding snapshots: {e}")
            snapshots = []

    else:
        print("Restore from snapshot not requested.")

        print("Reading data from BigQuery...")
        docs = query_bigquery(
            PUBLISHING_PROJECT_ID,
            query,
        )

        print(f"Creating collection {name} with {len(docs)} documents...")
        create_collection(client, name, size=768, distance_metric=Distance.COSINE)
        print(f"number of docs: {len(docs)}")

        # Convert data into PointStructs for upsertion
        points_to_upsert = create_vectors_from_data(
            docs, id_key="feedback_record_id", embedding_key="embeddings"
        )
        upsert_to_collection_from_vectors(client, name, data=points_to_upsert)
        print(
            f"Collection {name} created and upserted with {len(points_to_upsert)} points"
        )

        # TODO:Create snapshot on disk)
        client.create_snapshot(collection_name=name, wait=True)

    print(f"Collection {name} ready!")
