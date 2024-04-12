from src.utils.utils import load_qdrant_client
from src.utils.utils import load_model
from src.collection.evaluate_collection import (
    calculate_metrics,
)

from dotenv import load_dotenv
import os
import pickle
import numpy as np
import argparse

load_dotenv()

# Load env variables
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_PORT = os.getenv("QDRANT_PORT")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
HF_MODEL_NAME = os.getenv("HF_MODEL_NAME")
PUBLISHING_PROJECT_ID = os.getenv("PUBLISHING_PROJECT_ID")
EVALUATION_TABLE = os.getenv("EVALUATION_TABLE")
EVALUATION_TABLE = f"`{EVALUATION_TABLE}`"


def main(save_outputs: bool = False):
    # Load regex_ids
    with open("../data/regex_ids.pkl", "rb") as f:
        regex_ids = pickle.load(f)  # TODO: Probably add this download into this script

    # Load unique labels
    with open("../data/unique_labels.pkl", "rb") as f:
        unique_labels = pickle.load(f)

    # Load qdrant client and model
    qdrant = load_qdrant_client(QDRANT_HOST, port=QDRANT_PORT)
    model = load_model(HF_MODEL_NAME)

    # Loop over unique labels and similarity thresholds and return vals
    precision_values = []
    recall_values = []
    for unique_label in unique_labels:
        for threshold in np.arange(0, 1.1, 0.1):
            precision, recall = calculate_metrics(
                unique_label=unique_label,
                regex_ids=regex_ids,
                model=model,
                client=qdrant,
                similarity_threshold=threshold,
                collection_name=COLLECTION_NAME,
            )
            precision_values.append({unique_label: {threshold: precision}})
            recall_values.append({unique_label: {threshold: recall}})

    # Print first 10 values
    print(precision_values[:10])
    print(recall_values[:10])

    # pickle precision and recall values if argument is True
    if save_outputs:
        with open("../data/precision_values.pkl", "wb") as f:
            pickle.dump(precision_values, f)

        with open("../data/recall_values.pkl", "wb") as f:
            pickle.dump(recall_values, f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--save_outputs", type=bool, default=False)
    args = parser.parse_args()
    main(save_outputs=args.save_outputs)
