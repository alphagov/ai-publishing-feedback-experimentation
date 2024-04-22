from src.utils.utils import load_qdrant_client
from src.utils.utils import load_model
from src.collection_utils.evaluate_collection import process_labels

from dotenv import load_dotenv
import os
import pickle
import argparse
import subprocess

load_dotenv()

# Load env variables
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_PORT = os.getenv("QDRANT_PORT")
COLLECTION_NAME = os.getenv("EVAL_COLLECTION_NAME")
HF_MODEL_NAME = os.getenv("HF_MODEL_NAME")
PUBLISHING_PROJECT_ID = os.getenv("PUBLISHING_PROJECT_ID")
EVALUATION_TABLE = os.getenv("EVALUATION_TABLE")
EVALUATION_TABLE = f"`{EVALUATION_TABLE}`"


def main(save_outputs: bool = False):
    """
    Main function to get data for analysis and save the outputs as pickle files

    Requirements:
        Pickle files for unique labels and regex_ids. A Qdrant client and an encoder model.
    """
    if not os.path.exists("data/unique_labels.pkl") or not os.path.exists(
        "data/regex_ids.pkl"
    ):
        # run the evaluation/output_pkl.py script
        print("Running evaluation/output_pkl.py ...")
        subprocess.run(
            ["python", "-u", "evaluation/output_pkl.py", "--save_outputs", "True"]
        )

    # Load regex_ids
    with open("data/regex_ids.pkl", "rb") as f:
        regex_ids = pickle.load(f)

    # Load unique labels
    with open("data/unique_labels.pkl", "rb") as f:
        unique_labels = pickle.load(f)

    # Load Qdrant client and encoder model
    try:
        qdrant = load_qdrant_client(QDRANT_HOST, port=QDRANT_PORT)
        model = load_model(HF_MODEL_NAME)
    except Exception as e:
        print(f"Error: {e}")

    # Process labels
    precision_values, recall_values, f2_scores = process_labels(
        unique_labels=unique_labels,
        regex_ids=regex_ids,
        model=model,
        client=qdrant,
        collection_name=COLLECTION_NAME,
    )

    # # Loop over unique labels and similarity thresholds and return vals
    # precision_values = []
    # recall_values = []
    # f2_scores = []
    # batch_size = 100
    # num_batches = len(unique_labels) // batch_size + 1

    # for batch_idx in range(num_batches):
    #     start_idx = batch_idx * batch_size
    #     end_idx = min((batch_idx + 1) * batch_size, len(unique_labels))
    #     batch_labels = unique_labels[start_idx:end_idx]

    #     for unique_label in batch_labels:
    #         label_precision = {}
    #         label_recall = {}
    #         label_f2_scores = {}

    #         for threshold in np.arange(0, 1.1, 0.1):
    #             try:
    #                 precision, recall, f2_score = calculate_metrics(
    #                     unique_label=unique_label,
    #                     regex_ids=regex_ids,
    #                     model=model,
    #                     client=qdrant,
    #                     similarity_threshold=threshold,
    #                     collection_name=COLLECTION_NAME,
    #                 )
    #                 label_precision[threshold] = precision
    #                 label_recall[threshold] = recall
    #                 label_f2_scores[threshold] = f2_score
    #             except Exception as e:
    #                 print(
    #                     f"Error processing {unique_label} at threshold {threshold}: {e}"
    #                 )

    #         precision_values.append({unique_label: label_precision})
    #         recall_values.append({unique_label: label_recall})
    #         f2_scores.append({unique_label: label_f2_scores})
    #     print(f"Metrics calculated for labels index {start_idx} to {end_idx}")

    # Print first 10 values
    print(precision_values[:10])
    print(recall_values[:10])
    print(f2_scores[:10])

    # pickle precision and recall values if argument is True
    if save_outputs:
        with open("data/precision_values.pkl", "wb") as f:
            pickle.dump(precision_values, f)

        print("Precision values saved")

        with open("data/recall_values.pkl", "wb") as f:
            pickle.dump(recall_values, f)

        print("Recall values saved")

        with open("data/f2_scores.pkl", "wb") as f:
            pickle.dump(f2_scores, f)

        print("F2 scores saved")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--save_outputs", type=bool, default=False)
    args = parser.parse_args()
    main(save_outputs=args.save_outputs)
