import datetime
import os
import json

import streamlit as st
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

from src.collection.query_collection import get_top_k_results, filter_search
from src.common import keys_to_extract
from src.utils.call_openai_summarise import create_openai_summary
from src.utils.utils import process_csv_file, process_txt_file

from prompts.openai_summarise import system_prompt, user_prompt

# get env vars
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
FILTER_OPTIONS_PATH = os.getenv("FILTER_OPTIONS_PATH")
HF_MODEL_NAME = os.getenv("HF_MODEL_NAME")
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_PORT = os.getenv("QDRANT_PORT")

# config
similarity_score_threshold = 0.2
max_context_records = 20
min_records_for_summarisation = 5
k = 1000000  # Setting k -> inf as placeholder

st.set_page_config(layout="wide")


# Load the model only once, at the start of the app.
# TODO: Replace with call to HF Inferece API or OpenAI API
@st.cache_resource()
def load_qdrant_client(port):
    client = QdrantClient(QDRANT_HOST, port=port)
    return client


# Load the model only once, at the start of the app.
@st.cache_resource()
def load_model(model_name):
    model = SentenceTransformer(model_name)
    return model


@st.cache_resource()
def load_filter_dropdown_values(path_to_json):
    with open(path_to_json, "r") as file:
        data = json.load(file)
    return data


client = load_qdrant_client(QDRANT_PORT)
model = load_model(HF_MODEL_NAME)
filter_options = load_filter_dropdown_values(FILTER_OPTIONS_PATH)


def main():
    # Sidebar
    st.sidebar.image("data/gds-1024x669.png", width=250)
    st.sidebar.subheader("Feedback AI: Semantic Search and Summarisation\n")

    # Main content area
    st.title("Feedback AI Dashboard Prototype")
    st.subheader(
        "This dashboard uses a large language model to perform semantic search and return the most relevant feedback records, \
            together with a summary of the topics contained in the feedback."
    )

    # Free text box for one search term
    search_term_input = st.sidebar.text_input(
        "Enter a search term or phrase: \n (e.g. tax, Universal Credit, driving licence)"
    )
    search_terms = search_term_input.strip().lower()

    get_summary = st.sidebar.checkbox(
        "I would also like OpenAI to provide a summary of relevant feedback?"
    )

    st.sidebar.subheader("Filter your search\n")

    st.sidebar.write(
        "Below are filters to refine your search. You can filter your search by specific url (or parent page), urgency, organisation, document type and date range."
    )
    st.sidebar.write(
        "After choosing the appropriate filter values, hit 'Run Search...' to see the results."
    )

    user_input_pages = st.sidebar.multiselect(
        "Select URL from drop-down (e.g. '/browse/tax'):",
        filter_options["page_paths"],
        # max_selections=4,
        default=[],
    )

    include_child_pages = st.sidebar.checkbox(
        "Also include all child pages (e.g. 'browse/tax/...'?"
    )

    # File upload for list of URLs
    uploaded_url_file = st.sidebar.file_uploader(
        "Alternatively, upload a CSV of URLs to search", type=["txt", "csv"]
    )

    if uploaded_url_file is not None:
        # Determine the file type and process accordingly
        if uploaded_url_file.name.endswith(".txt"):
            user_input_pages = process_txt_file(uploaded_url_file) + user_input_pages
        elif uploaded_url_file.name.endswith(".csv"):
            user_input_pages = process_csv_file(uploaded_url_file) + user_input_pages
        else:
            st.error("Unsupported file type. Please upload a .txt or .csv file.")
            return

    # Find all urls in filter_options["urls"] that start with urls in matched_page_paths
    if user_input_pages and include_child_pages:
        all_pages = filter_options["page_paths"]

        matched_page_paths = [
            url
            for url in all_pages
            if url and any(url.startswith(path) for path in user_input_pages)
        ]
    elif not include_child_pages:
        matched_page_paths = user_input_pages
    else:
        matched_page_paths = []

    # Display the list of URLs
    st.write("URLs selected:")
    st.write(matched_page_paths)

    urgency_input = st.sidebar.multiselect(
        "Select urgency (Low:1, High:3, Unknown:-1):",
        ["1", "2", "3", "-1"],
        max_selections=4,
    )

    org_input = st.sidebar.multiselect(
        "Select organisation:", filter_options["orgs"], default=[]
    )

    doc_type_input = st.sidebar.multiselect(
        "Select document type:",
        filter_options["doc_types"],
        default=[],
    )

    # convert to int if not None, else keep as None
    urgency_input = [int(urgency) if urgency else None for urgency in urgency_input]

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

    filter_dict = {
        "url": matched_page_paths,
        "urgency": urgency_input,
        "department": org_input,
        "document_type": doc_type_input,
    }

    if st.sidebar.button("Run Search..."):
        if len(search_term_input) > 0:
            st.write("Running semantic search...")
            query_embedding = model.encode(search_terms)
            # Call the search function with filters
            search_results = get_top_k_results(
                client=client,
                collection_name=COLLECTION_NAME,
                query_embedding=query_embedding,
                k=k,
                filter_dict=filter_dict,
            )
            results = [dict(result) for result in search_results]
        elif len(search_term_input) == 0 and len(filter_dict["url"]) > 0:
            st.write("Running filter search...")
            # Call the filter function
            search_results = filter_search(
                client=client, collection_name=COLLECTION_NAME, filter_dict=filter_dict
            )
            data, _ = search_results
            results = [dict(result) for result in data]
        else:
            st.write(
                "Please supply a search term or terms and hit Apply Filters to see results..."
            )
            st.stop()

        filtered_list = []
        # Extract and append key-value pairs
        for result in results:
            payload = result["payload"]
            for key in payload:
                if key in keys_to_extract:  # Check if the key exists in keys_to_extract
                    result[key] = payload[key]

            result_ordered = {key: result[key] for key in keys_to_extract}
            result_ordered["score"] = result["score"] if "score" in result else float(1)
            result_ordered["payload"] = payload

            result_ordered["created_date"] = datetime.datetime.strptime(
                result_ordered["created"], "%Y-%m-%d"
            ).date()

            # Filter on date
            if (
                result_ordered["score"] > similarity_score_threshold
                and start_date <= result_ordered["created_date"] <= end_date
            ):
                filtered_list.append(result_ordered)

        st.write(f"{len(filtered_list)} relevant feedback records found...")

        # Topic summary where > n records returned
        # limiting to 20 records for context, to avoid token limits

        if get_summary and len(filtered_list) > min_records_for_summarisation:
            feedback_for_context = [record["feedback"] for record in filtered_list]
            summary = create_openai_summary(
                system_prompt,
                user_prompt,
                feedback_for_context[:max_context_records],
                OPENAI_API_KEY,
            )
            st.write(
                f"OpenAI Summary of relevant feedback based on {len(feedback_for_context)} records:"
            )
            st.write(summary["open_summary"])
        else:
            st.write(
                "Insufficient records for summarisation, or checkbox unchecked. For summary, check box and select a sufficient date range and search term."
            )
        st.write("------")
        st.write("Most relevant feedback records:")
        st.dataframe(filtered_list)
        st.success("Success")


if __name__ == "__main__":
    main()
