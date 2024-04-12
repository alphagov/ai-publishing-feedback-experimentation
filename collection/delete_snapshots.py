import os
from dotenv import load_dotenv

from src.collection_utils.set_collection import get_latest_snapshot_location
from src.utils.utils import load_qdrant_client

load_dotenv()
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
EVAL_COLLECTION_NAME = os.getenv("EVAL_COLLECTION_NAME")
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_PORT = os.getenv("QDRANT_PORT")

client = load_qdrant_client(QDRANT_HOST, port=QDRANT_PORT)

for name in [COLLECTION_NAME, EVAL_COLLECTION_NAME]:
    try:
        snapshots = client.list_snapshots(name)
        latest_snapshot = get_latest_snapshot_location(snapshots)
        # Clean up old snapshots
        for snapshot in snapshots:
            if snapshot.name != latest_snapshot:
                print(f"Deleting snapshot {snapshot.name}...")
                client.delete_snapshot(name, snapshot.name)

            elif snapshot.name == latest_snapshot and len(snapshots) == 1:
                print(f"Only latest snapshot remains for collection {name}")

    except Exception as e:
        print(f"Snapshots not found for collection {name}: {e}")
