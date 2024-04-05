import os

from dotenv import load_dotenv
from qdrant_client import QdrantClient

load_dotenv()
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_PORT = os.getenv("QDRANT_PORT")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
EVAL_COLLECTION_NAME = os.getenv("EVAL_COLLECTION_NAME")

client = QdrantClient(QDRANT_HOST, port=QDRANT_PORT)

collections = [COLLECTION_NAME, EVAL_COLLECTION_NAME]

for collection in collections:
    try:
        client.delete_collection(collection)
        print(f"Collection {collection} deleted")
    except Exception as e:
        print(f"Error deleting collection {collection}: {e}")
