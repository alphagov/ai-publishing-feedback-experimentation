from typing import List

import regex as re
from qdrant_client import QdrantClient

from src.collection_utils.query_collection import (
    filter_search,
    get_semantically_similar_results,
)
from src.sql_queries import query_evaluation_data
from src.utils.bigquery import query_bigquery
from src.utils.utils import load_model


def calculate_precision(retrieved_records: list, relevant_records: int) -> float:
    """
    Calculate precision

    Args:
        retrieved_records (int): Number of retrieved records
        relevant_records (int): Number of relevant records

    Returns:
        float: Precision
    """
    true_positives = len(set(retrieved_records).intersection(relevant_records))
    return true_positives / len(retrieved_records) if retrieved_records else 0


def calculate_recall(retrieved_records: dict, relevant_records: int) -> float:
    """
    Calculate recall

    Args:
        retrieved_records (int): Number of retrieved records
        relevant_records (int): Number of relevant records

    Returns:
        float: Recall
    """
    true_positives = len(set(retrieved_records).intersection(relevant_records))
    return true_positives / len(relevant_records) if relevant_records else 0


def calculate_f1_score(precision: dict, recall: int) -> float:
    """
    Calculate F1 score

    Args:
        precision (float): Precision
        recall (float): Recall

    Returns:
        float: F1 score
    """
    return (
        2 * (precision * recall) / (precision + recall)
        if (precision + recall) > 0
        else 0
    )


def calculate_f2_score(precision: dict, recall: int) -> float:
    """
    Calculate F2 score

    Args:
        precision (float): Precision
        recall (float): Recall

    Returns:
        float: F2 score
    """
    return (
        5 * (precision * recall) / (4 * precision + recall)
        if (4 * precision + recall) > 0
        else 0
    )


def get_data_for_evaluation(
    evaluation_table: str,
    project_id: str,
) -> List[dict]:
    """
    Query BQ for labelled feedback data. for use in evaluation.

    Args:
        evaluation_table (str): The name of the evaluation table.
        project_id (str): The project ID.

    Returns:
        list(dict): Feedback data IDs and labels
    """
    query = query_evaluation_data.replace("@EVALUATION_TABLE", evaluation_table)
    data = query_bigquery(
        project_id=project_id,
        query=query,
    )
    return data


def get_all_labels(data: List[dict]) -> str:
    """
    Get all labels from the feedback data.

    Args:
        data (List[dict]): The list of id, labels, and urgency.

    Returns:
        List[str]: The list of labels.
    """
    labels = []
    for record in data:
        for label in record["labels"].split(","):
            labels.append(label)
    return " ".join(labels)


def get_unique_labels(data: List[dict]) -> List[str]:
    """
    Get unique labels from the feedback data.

    Args:
        data (List[dict]): The list of id, labels, and urgency.

    Returns:
        List[str]: The list of unique labels.
    """
    unique_labels = set()
    for record in data:
        for label in record["labels"].split(","):
            unique_labels.add(label)
    unique_labels = [re.sub(r"[\[\]]", "", label) for label in unique_labels]
    unique_labels = [label.strip() for label in unique_labels]
    return list(unique_labels)


def get_regex_comparison(label: str, all_labels: str) -> int:
    """
    Given 1 label, use re.findall to get a regex count of how many records would
    be returned if we search for it.

    Args:
        label (str): A unique label to search for.
        all_labels (str): All labels joined together via whitespace.

    Returns:
        int: The number of matches.
    """
    matches = len(re.findall(label, all_labels, flags=re.IGNORECASE))
    return {"label": label, "n_matches": matches}


def get_all_regex_counts(data: List[dict]) -> dict:
    """
    Get the regex counts for all labels.

    Args:
        data (List[dict]): The list of id, labels, and urgency.

    Returns:
        List[dict]: The list of regex counts.
    """
    all_labels = get_all_labels(data)  # Get single string of all labels
    unique_labels = get_unique_labels(data)  # Get list of unique labels
    regex_counts = {}  # Initialise dict to store label and regex counts
    for unique_label in unique_labels:  # Loop through unique labels
        count = get_regex_comparison(unique_label, all_labels)  # Get regex count
        regex_counts[unique_label] = count  # Store in dict
    return regex_counts  # Return dict


def get_regex_ids(label: str, data: List[dict]) -> List[str]:
    """
    Given 1 label, use re.search to get a list of IDs that match the label.

    Args:
        label (str): A unique label to search for.
        data (List[dict]): The list of id, labels, and urgency.

    Returns:
        List[str]: The list of IDs that match the label.
    """
    ids = []
    for record in data:
        if re.search(label, record["labels"], flags=re.IGNORECASE):
            ids.append(record["id"])
    return ids


def get_all_regex_ids(data: List[dict]) -> dict:
    """
    Get the regex IDs for all labels.

    Args:
        data (List[dict]): The list of id, labels, and urgency.

    Returns:
        List[dict]: The list of regex IDs.
    """
    unique_labels = get_unique_labels(data)  # Get list of unique labels
    regex_ids = {}  # Initialise dict to store label and regex IDs
    for unique_label in unique_labels:  # Loop through unique labels
        ids = get_regex_ids(unique_label, data)  # Get regex IDs
        regex_ids[unique_label] = ids  # Store in dict
    return regex_ids  # Return dict


def assess_retrieval_accuracy(
    client: QdrantClient,
    collection_name: str,
    model_name: str,
    data: List[dict],
    score_threshold: float,
    regex_ids: dict,
) -> None:
    """
    Assess the retrieval accuracy of a collection by looping over all unique labels,
    retrieving the top K results for each label, and calculating precision, recall, and F1 score.

    Args:
        client (Any): The client object.
        collection_name (str): The name of the collection.
        data (List[dict]): The list of id, labels, and urgency.
        k_threshold (int): The threshold for retrieving top K results.
        regex_ids (dict): The dictionary of regex IDs.

    Returns:
        :List[str]: The list of result IDs.
    """

    # Load the model once
    model = load_model(model_name)

    # Get unique labels
    unique_labels = get_unique_labels(data)

    # Test using only unique labels[0]
    unique_labels = ["application"]

    # Retrieve top K results for each label
    for unique_label in unique_labels:
        # Get the count of records from the regex counts
        relevant_records = regex_ids[unique_label]

        # Embed the label
        query_embedding = model.encode(unique_label)

        # Retrieve the top K results for the label
        try:
            results = get_semantically_similar_results(
                client=client,
                collection_name=collection_name,
                query_embedding=query_embedding,
                score_threshold=score_threshold,
            )
        except Exception as e:
            print(f"get_semantically_similar_results error: {e}")
            continue

        result_ids = [str(result.id) for result in results]

        # Calculate precision, recall, F1, & F2 score
        precision = calculate_precision(result_ids, relevant_records)
        recall = calculate_recall(result_ids, relevant_records)
        f1_score = calculate_f1_score(precision, recall)
        f2_score = calculate_f2_score(precision, recall)

        # Print the results
        print(
            f"Label: {unique_label}, Precision: {precision: .3f}, \
              Recall: {recall: .3f}, F1 Score: {f1_score: .3f},   \
              F2 Score: {f2_score: .3f}"
        )
        return result_ids


def assess_scroll_retrieval(
    client: QdrantClient,
    collection_name: str,
    data: List[dict],
    regex_ids: dict,
):
    """
    Assess the retrieval accuracy of a collection by looping over all unique labels,
    and filtering the search results using MatchValue with a given string.

    Args:
        client (Any): The client object.
        collection_name (str): The name of the collection.
        data (List[dict]): The list of id, labels, and urgency.
        regex_ids (dict): The dictionary of regex IDs.

    Returns:
        :List[str]: The list of result IDs.
    """
    # Get unique labels
    unique_labels = get_unique_labels(data)

    # Test using only unique labels[0]
    unique_labels = ["application"]

    # Retrieve K results for each label using Scroll
    for unique_label in unique_labels:
        # Get the count of records from the regex counts
        relevant_records = regex_ids[unique_label]

        # Use get_top_scroll_results to query the label
        search_results = filter_search(
            client=client,
            collection_name=collection_name,
            filter_dict={"labels": [unique_label]},
        )

        results, _ = search_results

        if _ is not None:
            print(f"Possible more scroll results: {_}")

        result_ids = [str(result.id) for result in results]

        # Calculate precision, recall, F1, & F2 score
        precision = calculate_precision(result_ids, relevant_records)
        recall = calculate_recall(result_ids, relevant_records)
        f1_score = calculate_f1_score(precision, recall)
        f2_score = calculate_f2_score(precision, recall)

        # Print the results
        print(
            f"Label: {unique_label}, Precision: {precision: .3f}, \
            Recall: {recall: .3f}, F1 Score: {f1_score: .3f},   \
            F2 Score: {f2_score: .3f}"
        )

        return result_ids
