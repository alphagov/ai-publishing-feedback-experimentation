import os
import pickle
from src.collection.evaluate_collection import (
    assess_retrieval_accuracy,
    assess_scroll_retrieval,
    get_all_regex_counts,
    get_all_regex_ids,
    get_data_for_evaluation,
)
from src.utils.utils import load_config, load_qdrant_client

from dotenv import load_dotenv


load_dotenv()

# Get env vars
PUBLISHING_PROJECT_ID = os.getenv("PUBLISHING_PROJECT_ID")
EVALUATION_TABLE = os.getenv("EVALUATION_TABLE")
EVALUATION_TABLE = f"`{EVALUATION_TABLE}`"
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_PORT = os.getenv("QDRANT_PORT")
EVAL_COLLECTION_NAME = os.getenv("COLLECTION_NAME")
HF_MODEL_NAME = os.getenv("HF_MODEL_NAME")

config = load_config(".config/config.json")
similarity_threshold = float(config.get("similarity_threshold_1"))
print(f"Similarity threshold: {similarity_threshold}")

# Initialize a Qdrant client <- want to call our local client
client = load_qdrant_client(QDRANT_HOST, port=QDRANT_PORT)
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

# Save regex_counts as a pickle file
with open("regex_counts.pkl", "wb") as f:
    pickle.dump(regex_counts, f)

with open("regex_ids.pkl", "wb") as f:
    pickle.dump(regex_ids, f)

print("regex counts retrieved")

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

# Assess the scroll retrieval
scroll_results = assess_scroll_retrieval(
    client=client,
    collection_name=EVAL_COLLECTION_NAME,
    data=data,
    regex_ids=regex_ids,
)
print(f"Scroll n results: {len(scroll_results)}")
