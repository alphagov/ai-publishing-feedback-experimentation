from datetime import datetime

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, PointStruct, VectorParams


def create_vectors_from_data(documents: list[dict], id_key: str, embedding_key: str):
    """Create Qdrant vectors from numerical embeddings

    Args:
        documents (list[dict]): a list of documents in dicts
        id_key (str): name of the key containing the unique feedback id
        embedding_key (str): name of the key containing embeddings

    Returns:
        list[PointStruct]: list of vectors ready for upsert to collection
    """
    # Convert example data into PointStructs for upsertion
    embedding_vectors = []
    for record in documents:
        # Extract the embeddings and use them as the vector
        vector = record[embedding_key]
        # The feedback_record_id is used as the id for the point
        point_id = int(record[id_key])
        # Prepare the payload by excluding 'embeddings' and converting datetime to string
        payload = {
            key: (value.isoformat() if isinstance(value, datetime) else value)
            for key, value in record.items()
            if key != "embeddings"
        }
        # Create the PointStruct
        point = PointStruct(id=point_id, vector=vector, payload=payload)
        embedding_vectors.append(point)

    return embedding_vectors


def create_collection(
    client: QdrantClient,
    collection_name: str,
    size=768,
    distance_metric=Distance.DOT,
):
    """Create and upsert to a Qdrant collection

    Args:
        client (QdrantClient): the Qdrant client
        data (list[PointStruct]): list of vectors
        collection_name (str): name of the collection
        size (int, optional): _description_. Defaults to 768.
        distance_metric (_type_, optional): _description_. Defaults to Distance.DOT.
    """

    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=size, distance=distance_metric),
        on_disk_payload=True,
    )
    print(f"Collection {collection_name} created")


def upsert_to_collection_from_vectors(
    client: QdrantClient, collection_name: str, data: list[PointStruct]
):
    """Upsert data to Qdrant collection

    Args:
        collection_name (str): name of collection
        data (list[PointStruct]): vectors to upsert
    """

    def _chunk_data(data, chunk_size=100):
        """Chunk data into smaller pieces for upsertion"""
        for i in range(0, len(data), chunk_size):
            yield data[i : i + chunk_size]

    chunk_size = 500

    for chunk in _chunk_data(data, chunk_size=chunk_size):
        print(f"Upserting {len(chunk)} points to collection {collection_name}...")
        try:
            operation_info = client.upsert(
                collection_name=collection_name, wait=True, points=chunk
            )
            print(operation_info)
        except Exception as e:
            print(f"Error upserting to collection {collection_name}: {e}")
            print("Retrying upsertion...")
            try:
                operation_info = client.upsert(
                    collection_name=collection_name, wait=True, points=chunk
                )
                print(operation_info)
            except Exception as e:
                print(f"Error upserting to collection {collection_name} twice: {e}")


def get_latest_snapshot_location(snapshots: list) -> str:
    """
    Finds the location of the latest snapshot from a list of snapshot descriptions.

    Args:
        snapshots (List[SnapshotDescription]): A list of snapshot descriptions.

    Returns:
        str: The file location (name) of the latest snapshot.
    """
    # Convert the creation_time string to a datetime object for each snapshot and sort the list
    snapshots_sorted = sorted(
        snapshots,
        key=lambda snapshot: datetime.fromisoformat(snapshot.creation_time),
        reverse=True,
    )
    if snapshots_sorted:
        # Return the name of the latest snapshot
        return snapshots_sorted[0].name


def restore_collection_from_snapshot(
    client: QdrantClient,
    name: str,
    size: int,
    distance_metric: Distance,
):
    """Restore a collection from a snapshot

    Args:
        client (QdrantClient): Qdrant client
        name (str): name of the collection
        size (int): size of vectors in the collection
        distance_metric (Distance): distance metric used in the collection

    Returns:
        dict: Status and message of the operation
    """

    try:
        snapshots = client.list_snapshots(name)
        print(f"{len(snapshots)} snapshots found for collection {name}")
    except Exception:
        print(
            f"Unable to restore existing collection {name} from snapshot. Trying to create empty collection before searching again..."
        )
        try:
            create_collection(client, name, size=size, distance_metric=distance_metric)
            snapshots = client.list_snapshots(name)
        except Exception:
            return {
                "success": False,
                "message": f"Unable to restore collection {name} from snapshots via creating empty collection",
            }

    try:  # if able to find snapshots for this collection
        latest_snapshot = get_latest_snapshot_location(snapshots)
        client.recover_snapshot(
            name,
            location=f"file:///qdrant/snapshots/{name}/{latest_snapshot}",
            wait=True,
        )
        return {
            "success": True,
            "message": f"Collection {name} restored from snapshot {latest_snapshot}",
        }
    except Exception:
        print(f"No snapshots available for collection {name}")
        return {"success": False, "message": "No snapshots found"}
