import datetime
import os

import streamlit as st
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

from src.collection.query_collection import get_top_k_results
from src.common import keys_to_extract, rename_dictionary

# get env vars
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

st.set_page_config(layout="wide")


# Load the model only once, at the start of the app.
# TODO: Replace with call to HF Inferece API or OpenAI API
@st.cache_resource()
def load_qdrant_client(port):
    client = QdrantClient(os.getenv("QDRANT_HOST"), port=port)
    return client


# Load the model only once, at the start of the app.
@st.cache_resource()
def load_model(model_name):
    model = SentenceTransformer(model_name)
    return model


client = load_qdrant_client(6333)
model = load_model("all-mpnet-base-v2")

# Set any static variables for filtering retrieval
filter_key = "subject_page_path"


def main():
    # Sidebar
    st.sidebar.header("Settings")
    st.sidebar.write(
        "This dashboard uses a Sentence Transformer model to encode a search term and queries a Qdrant collection to return the most relevant records."
    )

    # Main content area
    st.title("Feedback AI Streamlit Dashboard Prototype")
    st.subheader("Semantic Search of Feedback")

    # Free text box for one search term
    # TODO: Enable batch search over a list of terms
    search_term_input = st.sidebar.text_input("Enter one search term: \n (e.g. tax)")
    search_terms = search_term_input.strip().lower()

    # Setting k -> inf as pLaceholder
    k = 1000000

    # Free text box for comma-separated list of subject pages.
    page_path_input = st.sidebar.text_input(
        "Enter optional subject page paths comma-separated: \n (e.g. /renew-medical-driving-licence)"
    )
    page_paths = (
        [item.strip() for item in page_path_input.split(",")] if page_path_input else []
    )

    # Date range slider in the sidebar.
    today = datetime.date.today()
    user_start_date = today - datetime.timedelta(
        days=90
    )  # Start date X days ago from today.
    user_end_date = today  # End date as today.

    date_range = st.sidebar.slider(
        "Select date range:",
        min_value=user_start_date,
        max_value=user_end_date,
        value=(user_start_date, user_end_date),
        format="DD/MM/YYYY",
    )

    start_date = date_range[0]
    end_date = date_range[1]

    st.sidebar.write("Selected range:", start_date, "to", end_date)

    if search_term_input:
        print(f"search terms: {search_terms}")
        query_embedding = model.encode(search_terms)
        print(type(query_embedding), len(query_embedding))
        # Call the search function with filters
        search_results = get_top_k_results(
            client=client,
            collection_name=COLLECTION_NAME,
            query_embedding=query_embedding,
            k=k,
            filter_key=filter_key,
            filter_values=page_paths,
        )
        results = [dict(result) for result in search_results]

        filtered_list = []
        # Extract and append key-value pairs
        for result in results:
            payload = result["payload"]
            for key in keys_to_extract:
                if key in payload:  # Check if the key exists in the payload
                    result[key] = payload[key]

            result = {key: result[key] for key in keys_to_extract}
            result["payload"] = payload
            result["created_date"] = datetime.datetime.strptime(
                result["created"], "%Y-%m-%d"
            ).date()

            # Rename keys
            output = {
                rename_dictionary[key]: result[key]
                for key in rename_dictionary
                if key in result
            }
            # Filter on date
            if start_date <= output["created_date"] <= end_date:
                filtered_list.append(output)

        st.write("Top k feedback records:")
        st.dataframe(filtered_list)
    else:
        st.write("Please supply a search term or terms")


if __name__ == "__main__":
    main()
