import os

from src.collection.evaluate_collection import (
    get_data_for_evaluation,
    load_qdrant_client,
    get_all_regex_counts,
    get_all_regex_ids,
    assess_retrieval_accuracy,
    assess_scroll_retrieval,
)

# Get env vars
PUBLISHING_PROJECT_ID = os.getenv("PUBLISHING_PROJECT_ID")
EVALUATION_TABLE = os.getenv("EVALUATION_TABLE")
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_PORT = os.getenv("QDRANT_PORT")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

# Initialize a Qdrant client <- want to call our local client
client = load_qdrant_client(qdrant_host="localhost", port=QDRANT_PORT)
print("client initiated")

# Get the data for evaluation <- still needs to be done
data = get_data_for_evaluation(
    project_id=PUBLISHING_PROJECT_ID,
    evaluation_table=EVALUATION_TABLE,
)
print("data retrieved")

# Get the regex counts and ids
regex_counts = get_all_regex_counts(data)
regex_ids = get_all_regex_ids(data)
print("regex counts retrieved")

# Assess the retrieval accuracy
ss_results = assess_retrieval_accuracy(
    client=client,
    collection_name=COLLECTION_NAME,
    data=data,
    k_threshold=1000000,
    regex_ids=regex_ids,
)
print(f"Dot product search n results: {len(ss_results)}")

# Assess the scroll retrieval
scroll_results = assess_scroll_retrieval(
    client=client,
    collection_name=COLLECTION_NAME,
    data=data,
    regex_ids=regex_ids,
)
print(f"Scroll n results: {len(scroll_results)}")
