import os

from src.collection.evaluate_collection import (
    assess_retrieval_accuracy,
    get_data_for_evaluation,
    get_all_regex_ids,
    assess_scroll_retrieval,
)
from src.utils.utils import load_qdrant_client

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

    regex_ids = get_all_regex_ids(data)

    # Assess the retrieval accuracy
    ss_results = assess_retrieval_accuracy(
        client=client,
        collection_name=COLLECTION_NAME,
        data=data,
        regex_ids=regex_ids,
        k_threshold=100,
    )
    print(f"Dot product search n results: {len(ss_results)}")

    # Assess the scroll retrieval accuracy
    scroll_results = assess_scroll_retrieval(
        client=client,
        collection_name=COLLECTION_NAME,
        data=data,
        regex_ids=regex_ids,
    )
    print(f"Scroll n results: {len(scroll_results)}")


if __name__ == "__main__":
    main()
