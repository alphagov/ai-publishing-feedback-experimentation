from src.collection.evaluate_collection import (
    get_data_for_evaluation,
    get_unique_labels,
    get_all_regex_counts,
    get_all_regex_ids,
)
import os
from dotenv import load_dotenv
import pickle

load_dotenv()

PUBLISHING_PROJECT_ID = os.getenv("PUBLISHING_PROJECT_ID")
EVALUATION_TABLE = os.getenv("EVALUATION_TABLE")
EVALUATION_TABLE = f"`{EVALUATION_TABLE}`"

# Get data for evaluation
data = get_data_for_evaluation(
    project_id=PUBLISHING_PROJECT_ID,
    evaluation_table=EVALUATION_TABLE,
)

# Get unique labels
unique_labels = get_unique_labels(data)

# Get the regex counts and ids
regex_counts = get_all_regex_counts(data)
regex_ids = get_all_regex_ids(data)

# Save regex_counts as a pickle file
with open("regex_counts.pkl", "wb") as f:
    pickle.dump(regex_counts, f)

with open("regex_ids.pkl", "wb") as f:
    pickle.dump(regex_ids, f)
