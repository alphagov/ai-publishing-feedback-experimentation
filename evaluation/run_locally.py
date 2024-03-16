import os

from src.collection.evaluate_collection import (
    get_data_for_evaluation,
    assess_retrieval_accuracy,
    get_regex_comparison,
    load_qdrant_client,
)

from dotenv import load_dotenv

load_dotenv()

# Get env vars
PUBLISHING_PROJECT_ID = os.getenv("PUBLISHING_PROJECT_ID")
EVALUATION_TABLE = os.getenv("EVALUATION_TABLE")
QDRANT_HOST = os.getenv("QDRANT_HOST")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

# Initialize a Qdrant client <- want to call our local client
client = load_qdrant_client(qdrant_host="localhost", port=6333)
print("client initiated")

# Get the data for evaluation <- still needs to be done
data = get_data_for_evaluation(
    project_id=PUBLISHING_PROJECT_ID,
    evaluation_table=EVALUATION_TABLE,
)

print("data retrieved")

regex_counts = get_regex_comparison(data=data)
print(regex_counts)

# # Assess the retrieval accuracy
assess_retrieval_accuracy(
    client=client,
    collection_name=COLLECTION_NAME,
    data=data,
    k_threshold=100,
)
