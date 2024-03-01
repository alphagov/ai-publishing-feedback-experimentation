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
QDRANT_PORT = os.getenv("QDRANT_PORT")

client = QdrantClient(
    "localhost", port=int(QDRANT_PORT)
)  # Set port number here to match your local docker container where qdrant is running

# Set any static variables for filtering retrieval
filter_key = "subject_page_path"


# Load the model only once, at the start of the app.
@st.cache_resource()
def load_model(model_name):
    model = SentenceTransformer(model_name)
    return model


model = load_model(HF_MODEL_NAME)


def main():
    # Sidebar
    st.sidebar.header("Settings")
    st.sidebar.text(
        "This dashboard uses a Sentence Transformer model to encode a search term and queries a Qdrant collection to return the most relevant records."
    )

    # Main content area
    st.title("Feedback AI Streamlit Dashboard Prototype")
    st.subheader("Subheading: Semantic Search of Feedback")

    # Free text box for one search term
    # TODO: Enable batch search over a list of terms
    search_term_input = st.sidebar.text_input("Enter one search term: \n (e.g. tax)")
    search_terms = search_term_input.strip().lower()

    # Free text box for comma-separated list of subject pages.
    page_path_input = st.sidebar.text_input(
        "Enter optional subject page paths comma-separated: \n (e.g. /renew-medical-driving-licence)"
    )
    page_paths = (
        [item.strip() for item in page_path_input.split(",")] if page_path_input else []
    )

    # Date range slider in the sidebar.
    today = datetime.date.today()
    start_date = today - datetime.timedelta(
        days=90
    )  # Start date X days ago from today.
    end_date = today  # End date as today.

    date_range = st.sidebar.slider(
        "Select date range (defunct):",
        min_value=start_date,
        max_value=end_date,
        value=(start_date, end_date),
        format="DD/MM/YYYY",
    )

    st.sidebar.write("Selected range:", date_range[0], "to", date_range[1])

    if search_term_input:
        print(f"search terms: {search_terms}")
        query_embedding = model.encode(search_terms)
        print(type(query_embedding), len(query_embedding))
        # Call the search function with filters
        search_results = get_top_k_results(
            client=client,
            collection_name=COLLECTION_NAME,
            query_embedding=query_embedding,
            k=5,
            filter_key=filter_key,
            filter_values=page_paths,
        )
        results = [dict(result) for result in search_results]
        st.write("Top k feedback records:")
        st.table(results)
    else:
        st.write("Please supply a search term or terms")


if __name__ == "__main__":
    main()
