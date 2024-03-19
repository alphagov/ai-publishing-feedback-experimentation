from qdrant_client import QdrantClient
from qdrant_client.http.models import FieldCondition, Filter, MatchValue


def get_top_k_results(
    client: QdrantClient,
    collection_name: str,
    query_embedding,
    k: int,
    filter_key=None,
    filter_values=[],
):  # TODO: Add return type
    """Retrieve top k results from collection

    Args:
        client (QdrantClient): The  Qdrant client.
        filter_key (str, optional): The key to filter the search over. Defaults to None.
        filter_values (list, optional): The values the filter can take. Defaults to [].

    Returns:
        list: the results of the search
    """
    # filter = Filter(
    #     must=[FieldCondition(key=filter_key, match=MatchAny(any=filter_values))]
    # )
    if filter_key and filter_values:
        search_result = client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            # query_filter=filter,
            limit=k,
        )
    else:
        search_result = client.search(
            collection_name=collection_name, query_vector=query_embedding, limit=k
        )

    return search_result


def get_top_scroll_results(
    client: QdrantClient,
    collection_name: str,
    input_string: str,
    variable_of_interest: str,
):  # TODO: replace object return type with actual return type
    """Retrieve all results from collection that contain a given string using
    Qdrant client.scroll and MatchValue with a given string. If we want to search
    for multiple values, we can use MatchAny with a list of values.

    Args:
        client (QdrantClient): The  Qdrant client.
        collection_name (str): The name of the collection.
        input_string (str): The string to search for.
        variable_of_interest (str): The key to filter the search over.

    Returns:
        list: the results of the search
    """
    search_result = client.scroll(
        collection_name=collection_name,
        scroll_filter=Filter(
            must=[
                FieldCondition(
                    key=variable_of_interest,
                    match=MatchValue(value=input_string),
                ),
            ]
        ),
        with_payload=["feedback_record_id", "response_value"],
        with_vectors=False,
    )

    data, _ = search_result
    return data
