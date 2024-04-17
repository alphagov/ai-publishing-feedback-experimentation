from src.collection_utils.evaluate_collection import (
    get_data_for_evaluation,
    get_unique_labels,
    get_all_regex_counts,
    get_all_regex_ids,
)
import os
from dotenv import load_dotenv
import pickle
import argparse

load_dotenv()

PUBLISHING_PROJECT_ID = os.getenv("PUBLISHING_PROJECT_ID")
EVALUATION_TABLE = os.getenv("EVALUATION_TABLE")
EVALUATION_TABLE = f"`{EVALUATION_TABLE}`"


def main(save_outputs: bool = False):
    """
    Main function to get data for evaluation and save the outputs as pickle files

    Requirements:
    A labelled BQ table with records and labels
    """
    print("Querying BQ ...")
    # Get data for evaluation
    try:
        data = get_data_for_evaluation(
            project_id=PUBLISHING_PROJECT_ID,
            evaluation_table=EVALUATION_TABLE,
        )
    except Exception as e:
        print(f"Error: {e}")

    # Get unique labels
    unique_labels = get_unique_labels(data)

    # Get the regex counts and ids
    regex_counts = get_all_regex_counts(data)
    regex_ids = get_all_regex_ids(data)

    if save_outputs:
        # Save regex_counts as a pickle file
        with open("data/regex_counts.pkl", "wb") as f:
            pickle.dump(regex_counts, f)
        # Save regex_ids as a pickle file
        with open("data/regex_ids.pkl", "wb") as f:
            pickle.dump(regex_ids, f)
        # Save unique_labels as a pickle file
        with open("data/unique_labels.pkl", "wb") as f:
            pickle.dump(unique_labels, f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--save_outputs", type=bool, default=False)
    args = parser.parse_args()
    main(save_outputs=args.save_outputs)
