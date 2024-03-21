import os

from src.collection.evaluate_collection import (
    assess_retrieval_accuracy,
    get_data_for_evaluation,
    load_qdrant_client,
)

# Get env vars
PUBLISHING_PROJECT_ID = os.getenv("PUBLISHING_PROJECT_ID")
EVALUATION_TABLE = os.getenv("EVALUATION_TABLE")
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_PORT = os.getenv("QDRANT_PORT")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")


def main():
    # Initialize a Qdrant client
    client = load_qdrant_client(QDRANT_HOST, port=QDRANT_PORT)

    # Get the data for evaluation
    data = get_data_for_evaluation(
        project_id=PUBLISHING_PROJECT_ID,
        evaluation_table=EVALUATION_TABLE,
    )

    # Assess the retrieval accuracy
    assess_retrieval_accuracy(
        client=client,
        collection_name=COLLECTION_NAME,
        labels=data,
        k_threshold=100,
    )


if __name__ == "__main__":
    main()
