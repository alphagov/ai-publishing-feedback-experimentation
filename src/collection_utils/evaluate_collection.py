from typing import List
from collections import defaultdict
import asyncio
import regex as re
from qdrant_client import QdrantClient
import numpy as np

from src.collection_utils.query_collection import (
    filter_search,
    async_get_semantically_similar_results,
    get_semantically_similar_results,
)
from src.sql_queries import query_evaluation_data
from src.utils.bigquery import query_bigquery
from src.utils.utils import load_model


def calculate_precision(retrieved_records: list, relevant_records: list) -> float:
    """
    Calculate precision

    Args:
        retrieved_records (list): list of retrieved records
        relevant_records (list): list of relevant records

    Returns:
        float: Precision
    """
    true_positives = len(set(retrieved_records).intersection(relevant_records))
    return true_positives / len(retrieved_records) if retrieved_records else 0


def calculate_recall(retrieved_records: list, relevant_records: list) -> float:
    """
    Calculate recall

    Args:
        retrieved_records (list): list of retrieved records
        relevant_records (list): list of relevant records

    Returns:
        float: Recall
    """
    true_positives = len(set(retrieved_records).intersection(relevant_records))
    return true_positives / len(relevant_records) if relevant_records else 0


def calculate_f1_score(precision: float, recall: float) -> float:
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


def calculate_f2_score(precision: float, recall: float) -> float:
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


def calculate_mean_values(data_list):
    # Dictionary to hold cumulative sums and counts for each test
    sums_counts = defaultdict(lambda: {"sum": 0, "count": 0})

    for item in data_list:
        for _, values in item.items():
            for threshold, value in values.items():
                sums_counts[threshold]["sum"] += value
                sums_counts[threshold]["count"] += 1

    # Calculate mean for each test
    mean_values = {
        test: info["sum"] / info["count"] for test, info in sums_counts.items()
    }
    return mean_values


def get_threshold_values(data, input_threshold=0.0):
    threshold_list = []
    for item in data:
        for threshold, value in item.items():
            if threshold == input_threshold:
                threshold_list.append(value)
    return threshold_list


def create_precision_boxplot_data(precision_values: list[dict]):
    """
    Create data for precision boxplot

    Args:
        precision_values (list): List of precision values

    Returns:
        dict: Dictionary of precision values"""
    # Drop the label from the dict
    precision_values = [list(item.values())[0] for item in precision_values]

    # Initialise empty dic
    precision_plotting_values = {}

    # Loop over threshold values and store the precision values in dict
    for i in np.arange(0, 1.1, 0.1):
        threshold_list = get_threshold_values(
            precision_values,
            input_threshold=i,
        )
        precision_plotting_values[i] = threshold_list

    # Round the keys to 2 decimal places
    rounded_precision_values = {
        round(key, 2): value for key, value in precision_plotting_values.items()
    }
    return rounded_precision_values


def create_recall_boxplot_data(recall_values: list[dict]):
    """
    Create data for recall boxplot

    Args:
        recall_values (list): List of recall values

    Returns:
        dict: Dictionary of recall values"""
    # Drop the label from the dict
    recall_values = [list(item.values())[0] for item in recall_values]

    # Initialise empty dict
    recall_plotting_values = {}

    # Loop over threshold values and store the recall values in dict
    for i in np.arange(0, 1.1, 0.1):
        threshold_list = get_threshold_values(
            recall_values,
            input_threshold=i,
        )
        recall_plotting_values[i] = threshold_list

    # Round the keys to 2 decimal places
    rounded_precision_values = {
        round(key, 2): value for key, value in recall_plotting_values.items()
    }
    return rounded_precision_values


def create_precision_line_data(precision_values: list[dict]):
    """
    Create data for precision line plot

    Args:
        precision_values (list): List of precision values

    Returns:
        dict: Dictionary of precision values"""
    # Calculate mean values for each threshold
    mean_precision_values = calculate_mean_values(precision_values)
    # Round the keys and values to 2 decimal places
    mean_precision_values = {
        round(k, 2): round(v, 2) for k, v in mean_precision_values.items()
    }
    return mean_precision_values


def create_recall_line_data(recall_values: list[dict]):
    """
    Create data for recall line plot

    Args:
        recall_values (list): List of recall values

    Returns:
        dict: Dictionary of recall values"""
    # Calculate mean values for each threshold
    mean_recall_values = calculate_mean_values(recall_values)
    # Round the keys and values to 2 decimal places
    mean_recall_values = {
        round(k, 2): round(v, 2) for k, v in mean_recall_values.items()
    }
    return mean_recall_values


def create_f2_line_data(f2_values: list[dict]):
    """
    Create data for F2 line plot

    Args:
        f2_values (list): List of F2 values

    Returns:
        dict: Dictionary of F2 values"""
    # Calculate mean values for each threshold
    mean_f2_values = calculate_mean_values(f2_values)
    # Round the keys and values to 2 decimal places
    mean_f2_values = {round(k, 2): round(v, 2) for k, v in mean_f2_values.items()}
    return mean_f2_values


async def async_calculate_metrics(
    unique_label: str,
    regex_ids: dict,
    model: object,
    client: object,
    similarity_threshold: float,
    collection_name: str,
):
    """
    Calculate precision, recall and f2 score for a given label

    Args:
        unique_label (str): The unique label
        regex_ids (dict): The dictionary of regex IDs
        model (Any): The model object
        client (Any): The client object
        similarity_threshold (float): The similarity threshold
        collection_name (str): The name of the collection

    Returns:
        float: Precision
        float: Recall
        float: F2 score
    """
    # Get the count of records from the regex counts
    relevant_records = regex_ids[unique_label]

    # Embed the label
    query_embedding = model.encode(unique_label)

    # Retrieve the top K results for the label
    try:
        results = await async_get_semantically_similar_results(
            client,
            collection_name,
            query_embedding,
            similarity_threshold,
        )

    except Exception as e:
        print(f"get_semantically_similar_results error for {unique_label}: {e}")
        return None, None, None

    result_ids = [str(result.id) for result in results]

    # Calculate precision and recall
    precision = calculate_precision(result_ids, relevant_records)
    recall = calculate_recall(result_ids, relevant_records)
    f2_score = calculate_f2_score(precision, recall)

    return precision, recall, f2_score


# TODO: this function takes ages even though it's async, why? I'm probably not asyncing each batch, rather the whole thing?
# async def process_labels(unique_labels, regex_ids, model, client, collection_name):
#     precision_values = []
#     recall_values = []
#     f2_scores = []
#     batch_size = 100
#     num_batches = len(unique_labels) // batch_size + 1

#     for batch_idx in range(num_batches):
#         start_idx = batch_idx * batch_size
#         end_idx = min((batch_idx + 1) * batch_size, len(unique_labels))
#         batch_labels = unique_labels[start_idx:end_idx]

#         for unique_label in batch_labels:
#             label_precision = {}
#             label_recall = {}
#             label_f2_scores = {}

#             for threshold in np.arange(0, 1.1, 0.1):
#                 try:
#                     precision, recall, f2_score = await async_calculate_metrics(
#                         unique_label=unique_label,
#                         regex_ids=regex_ids,
#                         model=model,
#                         client=client,
#                         similarity_threshold=threshold,
#                         collection_name=collection_name,
#                     )
#                     label_precision[threshold] = precision
#                     label_recall[threshold] = recall
#                     label_f2_scores[threshold] = f2_score
#                 except Exception as e:
#                     print(
#                         f"Error processing {unique_label} at threshold {threshold}: {e}"
#                     )

#             precision_values.append({unique_label: label_precision})
#             recall_values.append({unique_label: label_recall})
#             f2_scores.append({unique_label: label_f2_scores})
#         print(f"Metrics calculated for labels: {start_idx} to {end_idx}")

#     return precision_values, recall_values, f2_scores


async def process_single_label(unique_label, regex_ids, model, client, collection_name):
    label_precision = {}
    label_recall = {}
    label_f2_scores = {}

    for threshold in np.arange(0, 1.1, 0.1):
        try:
            precision, recall, f2_score = await async_calculate_metrics(
                unique_label=unique_label,
                regex_ids=regex_ids,
                model=model,
                client=client,
                similarity_threshold=threshold,
                collection_name=collection_name,
            )
            label_precision[threshold] = precision
            label_recall[threshold] = recall
            label_f2_scores[threshold] = f2_score
        except Exception as e:
            print(f"Error processing {unique_label} at threshold {threshold}: {e}")

    return {
        "precision": {unique_label: label_precision},
        "recall": {unique_label: label_recall},
        "f2_scores": {unique_label: label_f2_scores},
    }


async def process_labels(unique_labels, regex_ids, model, client, collection_name):
    tasks = [
        process_single_label(label, regex_ids, model, client, collection_name)
        for label in unique_labels
    ]
    results = await asyncio.gather(*tasks)

    precision_values = [result["precision"] for result in results]
    recall_values = [result["recall"] for result in results]
    f2_scores = [result["f2_scores"] for result in results]

    return precision_values, recall_values, f2_scores
