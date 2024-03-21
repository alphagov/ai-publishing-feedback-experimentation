from qdrant_client import QdrantClient
from qdrant_client.http.models import FieldCondition, Filter, MatchAny


def get_top_k_results(
    client: QdrantClient, collection_name: str, query_embedding, k: int, filter_dict={}
):
    """Retrieve top k results from collection

    Args:
        client (QdrantClient): The  Qdrant client.
        collection_name (str): The name of the collection.
        query_embedding (list): The query vector.
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

    print(filter)

    if len(filter_dict) > 0:
        search_result = client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            query_filter=filter,
            limit=k,
        )
    else:
        search_result = client.search(
            collection_name=collection_name, query_vector=query_embedding, limit=k
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
            collection_name=collection_name, scroll_filter=filter
        )
        return search_result
    else:
        print("No filters present, provide filters to search")
