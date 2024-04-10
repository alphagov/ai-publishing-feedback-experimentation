import os

from dotenv import load_dotenv
from qdrant_client import QdrantClient


load_dotenv()
QDRANT_HOST = os.getenv("QDRANT_HOST_EXTERNAL")
QDRANT_PORT = os.getenv("QDRANT_PORT")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
EVAL_COLLECTION_NAME = os.getenv("EVAL_COLLECTION_NAME")

print(QDRANT_HOST[:2])
print(QDRANT_PORT[:2])
print(COLLECTION_NAME[:2])

client = QdrantClient(QDRANT_HOST, port=QDRANT_PORT)

print(client.get_collections())
