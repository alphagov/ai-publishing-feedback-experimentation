import os
import pickle
from src.collection.evaluate_collection import (
    assess_retrieval_accuracy,
    get_data_for_evaluation,
    assess_scroll_retrieval,
)
from src.utils.utils import load_qdrant_client, load_config

# Get env vars
PUBLISHING_PROJECT_ID = os.getenv("PUBLISHING_PROJECT_ID")
EVALUATION_TABLE = os.getenv("EVALUATION_TABLE")
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_PORT = os.getenv("QDRANT_PORT")
EVAL_COLLECTION_NAME = os.getenv("EVAL_COLLECTION_NAME")
HF_MODEL_NAME = os.getenv("HF_MODEL_NAME")

config = load_config(".config/config.json")
similarity_threshold = float(config.get("dot_product_threshold_1"))
print(f"Similarity threshold: {similarity_threshold}")


def main():
    # Initialize a Qdrant client
    client = load_qdrant_client(QDRANT_HOST, port=QDRANT_PORT)

    # Read in the data for evaluation
    data = get_data_for_evaluation(
        project_id=PUBLISHING_PROJECT_ID,
        evaluation_table=EVALUATION_TABLE,
    )

    # Read data_regex_counts.pkl
    with open("data/regex_counts.pkl", "rb") as f:
        regex_counts = pickle.load(f)

    with open("data/regex_ids.pkl", "rb") as f:
        regex_ids = pickle.load(f)

    # Assess the retrieval accuracy
    ss_results = assess_retrieval_accuracy(
        client=client,
        collection_name=EVAL_COLLECTION_NAME,
        model_name=HF_MODEL_NAME,
        data=data,
        regex_ids=regex_ids,
        score_threshold=similarity_threshold,
    )
    print(f"Dot product search n results: {len(ss_results)}")

    # Assess the scroll retrieval accuracy
    scroll_results = assess_scroll_retrieval(
        client=client,
        collection_name=EVAL_COLLECTION_NAME,
        data=data,
        regex_ids=regex_ids,
    )
    print(f"Scroll n results: {len(scroll_results)}")


if __name__ == "__main__":
    main()
