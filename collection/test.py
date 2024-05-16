import os

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import FieldCondition, Filter, MatchAny


load_dotenv()
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_PORT = os.getenv("QDRANT_PORT")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
EVAL_COLLECTION_NAME = os.getenv("EVAL_COLLECTION_NAME")

print(QDRANT_HOST[:2])
print(QDRANT_PORT[:2])
print(COLLECTION_NAME[:2])

client = QdrantClient(QDRANT_HOST, port=QDRANT_PORT)

print(client.get_collections())


filter_dict = {"primary_department": ["Government Digital Service"]}
filter = Filter(
    must=[
        FieldCondition(key=filter_key, match=MatchAny(any=filter_values))
        for filter_key, filter_values in filter_dict.items()
        if filter_values
    ]
)

test_results = client.scroll(
    collection_name=COLLECTION_NAME,
    scroll_filter=filter,
    limit=10,
)
print(len(test_results))
