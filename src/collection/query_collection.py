from qdrant_client import QdrantClient
from qdrant_client.http.models import FieldCondition, Filter, MatchAny


# search collection
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
        client (QdrantClient): _description_
        filter_key (_type_, optional): _description_. Defaults to None.
        filter_values (list, optional): _description_. Defaults to [].

    Returns:
        _type_: _description_
    """
    if filter_key and filter_values:
        search_result = client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            query_filter=Filter(
                must=[FieldCondition(key=filter_key, match=MatchAny(any=filter_values))]
            ),
            limit=3,
        )
    else:
        search_result = client.search(
            collection_name=collection_name, query_vector=query_embedding, limit=3
        )

    return search_result


#  eval fn versus labels
