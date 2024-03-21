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
