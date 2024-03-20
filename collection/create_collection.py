import os

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance

from src.collection.set_collection import (
    create_collection,
    create_vectors_from_data,
    upsert_to_collection_from_vectors,
)
from src.sql_queries import query_labelled_feedback
from src.utils.bigquery import query_bigquery

PUBLISHING_PROJECT_ID = os.getenv("PUBLISHING_PROJECT_ID")
LABELLED_FEEDBACK_TABLE = os.getenv("EVALUATION_TABLE")
PUBLISHING_VIEW = os.getenv("PUBLISHING_VIEW")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_PORT = os.getenv("QDRANT_PORT")


query_read = query_labelled_feedback.replace(
    "@LABELLED_FEEDBACK_TABLE", str(LABELLED_FEEDBACK_TABLE)
).replace("@PUBLISHING_VIEW", str(PUBLISHING_VIEW))

# Call the function to execute the query
docs = query_bigquery(
    PUBLISHING_PROJECT_ID,
    query_read,
)

client = QdrantClient(QDRANT_HOST, port=QDRANT_PORT)

# Create collection
create_collection(client, COLLECTION_NAME, size=768, distance_metric=Distance.DOT)

print(f"number of docs: {len(docs)}")

# Convert data into PointStructs for upsertion
points_to_upsert = create_vectors_from_data(
    docs, id_key="feedback_record_id", embedding_key="embeddings"
)

# Upsert data to collection
upsert_to_collection_from_vectors(client, COLLECTION_NAME, data=points_to_upsert)
