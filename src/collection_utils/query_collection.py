from qdrant_client import QdrantClient

from qdrant_client.http.models import FieldCondition, Filter, MatchAny


def get_semantically_similar_results(
    client: QdrantClient,
    collection_name: str,
    query_embedding,
    score_threshold: float,
    filter_dict={},
):
    """Retrieve top k results from collection

    Args:
        client (QdrantClient): The  Qdrant client.
        collection_name (str): The name of the collection.
        query_embedding (list): The query vector.
        score_threshold (float): The minimum score to return.
        filter_dict (dict, optional): The keys and values to filter on. Defaults to {}.

    Returns:
        list: the results of the search
    """
    filter = Filter(
        must=[
            FieldCondition(key=filter_key, match=MatchAny(any=filter_values))
            for filter_key, filter_values in filter_dict.items()
            if filter_values
        ]
    )

    if len(filter_dict) > 0:
        search_result = client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            query_filter=filter,
            score_threshold=score_threshold,
            limit=10000000,
            timeout=10000,
        )
    else:
        search_result = client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            score_threshold=score_threshold,
            limit=10000000,
            timeout=10000,
        )

    return search_result


def filter_search(client: QdrantClient, collection_name: str, filter_dict: dict):
    """Query collection using filter alone

    Args:
        client (QdrantClient): The  Qdrant client.
        collection_name (str): The name of the collection.
        filter_dict (dict): The keys and values to filter on. Defaults to {}.

    Returns:
        list: the results of the search
    """
    filter = Filter(
        must=[
            FieldCondition(key=filter_key, match=MatchAny(any=filter_values))
            for filter_key, filter_values in filter_dict.items()
            if filter_values
        ]
    )
    if len(filter_dict) > 0:
        search_result = client.scroll(
            collection_name=collection_name,
            scroll_filter=filter,
            limit=10000000,
        )
        return search_result
    else:
        print("No filters present, provide filters to search")
