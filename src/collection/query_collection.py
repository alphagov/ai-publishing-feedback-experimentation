from qdrant_client import QdrantClient
from qdrant_client.http.models import FieldCondition, Filter, MatchAny


def get_top_k_results(
    client: QdrantClient,
    collection_name: str,
    query_embedding,
    k: int,
    filter_key=None,
    filter_values=[],
):
    """Retrieve top k results from collection

    Args:
        client (QdrantClient): The  Qdrant client.
        filter_key (str, optional): The key to filter the search over. Defaults to None.
        filter_values (list, optional): The values the filter can take. Defaults to [].

    Returns:
        list: the results of the search
    """
    filter = Filter(
        must=[FieldCondition(key=filter_key, match=MatchAny(any=filter_values))]
    )
    if filter_key and filter_values:
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
