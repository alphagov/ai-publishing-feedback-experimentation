import datetime
import os

import streamlit as st
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

from src.collection.query_collection import get_top_k_results

# get env vars
PUBLISHING_PROJECT_ID = os.getenv("PUBLISHING_PROJECT_ID")
LABELLED_FEEDBACK_DATASET = os.getenv("LABELLED_FEEDBACK_DATASET")
PUBLISHING_VIEW = os.getenv("PUBLISHING_VIEW")
OPENAI_LABELLED_FEEDBACK_TABLE = os.getenv("OPENAI_LABELLED_FEEDBACK_TABLE")
HF_MODEL_NAME = os.getenv("HF_MODEL_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")


# Load the model only once, at the start of the app.
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
    st.sidebar.text(
        "This dashboard uses a Sentence Transformer model to encode a search term and queries a Qdrant collection to return the most relevant records."
    )

    # Main content area
    st.title("Feedback AI Streamlit Dashboard Prototype")
    st.subheader("Semantic Search of Feedback")

    # Free text box for one search term
    # TODO: Enable batch search over a list of terms
    search_term_input = st.sidebar.text_input("Enter one search term: \n (e.g. tax)")
    search_terms = search_term_input.strip().lower()

    k = st.sidebar.slider(
        "Select number of results to return:",
        min_value=0,
        max_value=50,
        value=10,  # Default value
        step=1,  # Increment the slider by integers
    )

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
        "Select date range (defunct):",
        min_value=user_start_date,
        max_value=user_end_date,
        value=(user_start_date, user_end_date),
        format="DD/MM/YYYY",
    )

    start_datetime = datetime.datetime.combine(date_range[0], datetime.time(0, 0, 0))
    end_datetime = datetime.datetime.combine(date_range[1], datetime.time(23, 59, 59))

    print(start_datetime, end_datetime)
    st.sidebar.write("Selected range:", end_datetime, "to", end_datetime)

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
        for d in results:
            result = d.copy()
            payload = result.pop("payload", {})
            # Merge payload key-value pairs into the top-level dictionary
            result.update(payload)

            result["created_dt"] = datetime.datetime.strptime(
                result["created"][:19], "%Y-%m-%dT%H:%M:%S"
            )
            # Filter on date
            if start_datetime <= result["created_dt"] <= end_datetime:
                filtered_list.append(result)

        st.write("Top k feedback records:")
        st.table(filtered_list)
    else:
        st.write("Please supply a search term or terms")


if __name__ == "__main__":
    main()
