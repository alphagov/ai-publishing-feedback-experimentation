import os
from src.utils.bigquery import query_bigquery
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance

from src.sql_queries import query_labelled_feedback

from src.collection.set_collection import (
    create_vectors_from_data,
    create_collection,
    upsert_to_collection_from_vectors,
)

PUBLISHING_PROJECT_ID = os.getenv("PUBLISHING_PROJECT_ID")
LABELLED_FEEDBACK_DATASET = os.getenv("LABELLED_FEEDBACK_DATASET")
PUBLISHING_VIEW = os.getenv("PUBLISHING_VIEW")
OPENAI_LABELLED_FEEDBACK_TABLE = os.getenv("OPENAI_LABELLED_FEEDBACK_TABLE")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

print(str(OPENAI_LABELLED_FEEDBACK_TABLE))
print(OPENAI_LABELLED_FEEDBACK_TABLE)

query_read = query_labelled_feedback.replace(
    "@labelled_feedback_table", str(OPENAI_LABELLED_FEEDBACK_TABLE)
).replace("@PUBLISHING_VIEW", str(PUBLISHING_VIEW))

print(query_read)

# Call the function to execute the query
docs = query_bigquery(
    PUBLISHING_PROJECT_ID,
    LABELLED_FEEDBACK_DATASET,
    query_read,
)

client = QdrantClient("localhost", port=6333)

# Create collection
create_collection(client, COLLECTION_NAME, size=768, distance_metric=Distance.DOT)

# Convert data into PointStructs for upsertion
points_to_upsert = create_vectors_from_data(
    docs, id_key="feedback_record_id", embedding_key="embeddings"
)

# Upsert data to collection
upsert_to_collection_from_vectors(client, COLLECTION_NAME, data=points_to_upsert)
