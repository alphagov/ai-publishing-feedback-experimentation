import os

from qdrant_client.http.models import Distance

from src.collection.set_collection import (
    create_collection,
    create_vectors_from_data,
    upsert_to_collection_from_vectors,
)
from src.sql_queries import query_labelled_feedback, query_all_feedback
from src.utils.bigquery import query_bigquery
from src.utils.utils import load_qdrant_client, load_config

PUBLISHING_PROJECT_ID = os.getenv("PUBLISHING_PROJECT_ID")
LABELLED_FEEDBACK_TABLE = os.getenv("EVALUATION_TABLE")
PUBLISHING_VIEW = os.getenv("PUBLISHING_VIEW")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
EVAL_COLLECTION_NAME = os.getenv("EVAL_COLLECTION_NAME")
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_PORT = os.getenv("QDRANT_PORT")

config = load_config(".config/config.json")


all_query_read = query_all_feedback.replace("@PUBLISHING_VIEW", str(PUBLISHING_VIEW))

eval_query_read = query_labelled_feedback.replace(
    "@LABELLED_FEEDBACK_TABLE", str(LABELLED_FEEDBACK_TABLE)
).replace("@PUBLISHING_VIEW", str(PUBLISHING_VIEW))

print("Reading data from BigQuery...")

# Call the function to get all feedback
feedback_docs = query_bigquery(
    PUBLISHING_PROJECT_ID,
    all_query_read,
)

# Call the function to get labelled feedback for evaluation
eval_docs = query_bigquery(
    PUBLISHING_PROJECT_ID,
    eval_query_read,
)

client = load_qdrant_client(QDRANT_HOST, port=QDRANT_PORT)

# Create feedback and eval collections
for name, docs in [(COLLECTION_NAME, feedback_docs), (EVAL_COLLECTION_NAME, eval_docs)]:
    print(f"Creating collection {name} with {len(docs)} documents...")
    create_collection(client, name, size=768, distance_metric=Distance.DOT)
    print(f"number of docs: {len(docs)}")

    # Convert data into PointStructs for upsertion
    points_to_upsert = create_vectors_from_data(
        docs, id_key="feedback_record_id", embedding_key="embeddings"
    )
    upsert_to_collection_from_vectors(client, name, data=points_to_upsert)
    print(f"Collection {name} created and upserted with {len(points_to_upsert)} points")
