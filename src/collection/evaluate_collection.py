from src.collection.query_collection import get_top_k_results, filter_search
from sentence_transformers import SentenceTransformer
from typing import List
from qdrant_client import QdrantClient
from src.utils.bigquery import query_bigquery
import regex as re


def load_qdrant_client(qdrant_host: str, port: int) -> QdrantClient:
    client = QdrantClient(qdrant_host, port=port)
    return client


def load_model(model_name: str) -> SentenceTransformer:
    """
    Load the SentenceTransformer model.

    Args:
        model_name (str): The name of the model.

    Returns:
        SentenceTransformer: The loaded model.
    """
    model = SentenceTransformer(model_name)
    return model


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
    print(f"true_positives: {true_positives}")
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
) -> dict:
    """
    Query BQ for labelled feedback data. for use in evaluation.

    Returns:
        list(dict): Feedback data IDs and labels
    """
    query = """
    SELECT
        id,
        ARRAY_TO_STRING(labels, ", ") as labels,
        urgency
    FROM
        @evaluation_table
    """
    query = query.replace("@evaluation_table", evaluation_table)
    data = query_bigquery(
        project_id=project_id,
        query=query,
    )
    return data  # TODO: Check if this is the correct return type


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


def assess_retrieval_accuracy(
    client: QdrantClient,
    collection_name: str,
    data: List[dict],
    k_threshold: int,
    regex_counts: dict,
) -> None:
    """
    Assess the retrieval accuracy of a collection by looping over all unique labels,
    retrieving the top K results for each label, and calculating precision, recall, and F1 score.

    Args:
        client (Any): The client object.
        collection_name (str): The name of the collection.
        data (List[dict]): The list of id, labels, and urgency.
        k_threshold (int): The threshold for retrieving top K results.

    Returns:
        None
    """

    # Load the model once
    model = load_model("all-mpnet-base-v2")

    # Get unique labels
    unique_labels = get_unique_labels(data)

    # Test using only unique labels[0]
    unique_labels = ["application"]

    # Retrieve top K results for each label
    for unique_label in unique_labels:
        # Get the count of records from the regex counts
        relevant_records = regex_counts[unique_label]["n_matches"]

        # Embed the label
        query_embedding = model.encode(unique_label)

        # Retrieve the top K results for the label
        try:
            results = get_top_k_results(
                client=client,
                collection_name=collection_name,
                query_embedding=query_embedding,
                k=k_threshold,
            )
        except Exception as e:
            print(f"get_top_k_results error: {e}")
            continue

        result_ids = [result.id for result in results]

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
    regex_counts: dict,
):
    """
    Assess the retrieval accuracy of a collection by looping over all unique labels,
    and filtering the search results using MatchValue with a given string.

    Args:
        client (Any): The client object.
        collection_name (str): The name of the collection.
        data (List[dict]): The list of id, labels, and urgency.

    Returns:
        None
    """
    # Get unique labels
    unique_labels = get_unique_labels(data)

    # Test using only unique labels[0]
    unique_labels = ["application"]

    # Retrieve K results for each label using Scroll
    for unique_label in unique_labels:
        # Get the count of records from the regex counts
        relevant_records = regex_counts[unique_label]["n_matches"]

        # Use get_top_scroll_results to query the label
        search_results = filter_search(
            client=client,
            collection_name=collection_name,
            filter_dict={"labels": [unique_label]},
        )

        results, _ = search_results

        if _ is not None:
            print(f"Possible more scroll results: {_}")

        result_ids = [result.id for result in results]

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
