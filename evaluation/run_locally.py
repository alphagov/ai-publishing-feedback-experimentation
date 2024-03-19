import os

from src.collection.evaluate_collection import (
    get_data_for_evaluation,
    load_qdrant_client,
    get_all_regex_counts,
    assess_retrieval_accuracy,
    assess_scroll_retrieval,
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

# Get the regex counts
regex_counts = get_all_regex_counts(data)
print(f"length of regex counts: {regex_counts["application"]["n_matches"]}")
print("regex counts retrieved")

# Assess the retrieval accuracy
ss_results = assess_retrieval_accuracy(
    client=client,
    collection_name=COLLECTION_NAME,
    data=data,
    k_threshold=1000000,
)
print(f"Dot product search n results: {len(ss_results)}")

# Assess the scroll retrieval
scroll_results = assess_scroll_retrieval(
    client=client,
    collection_name=COLLECTION_NAME,
    data=data,
)
print(f"Scroll n results: {len(scroll_results)}")
print(f"Are scroll and ss results the same? {scroll_results == ss_results}")
