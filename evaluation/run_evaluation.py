from src.collection.evaluate_collection import (
    load_qdrant_client,
    get_data_for_evaluation,
    assess_retrieval_accuracy,
)
import os
from dotenv import load_dotenv

load_dotenv()

# Get env vars
PROJECT_ID = os.getenv("PROJECT_ID")
EVALUATION_DATASET = os.getenv("EVALUATION_DATASET")
QDRANT_HOST = os.getenv("QDRANT_HOST")

# Initialize a Qdrant client
client = load_qdrant_client(host=QDRANT_HOST, port=6333)

# Get the data for evaluation
data = get_data_for_evaluation(
    project_id=PROJECT_ID,
    evaluation_dataset=EVALUATION_DATASET,
)
print(data)

# Assess the retrieval accuracy
assess_retrieval_accuracy(
    client=client,
    collection_name="feedback_collection",
    labels=data,
    k_threshold=10,
)
