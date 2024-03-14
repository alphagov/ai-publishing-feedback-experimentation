import datetime
import os
import json

import streamlit as st
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

from src.collection.query_collection import get_top_k_results
from src.common import keys_to_extract, rename_dictionary
from src.utils.call_openai_summarise import create_openai_summary

from prompts.openai_summarise import system_prompt, user_prompt

# get env vars
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
FILTER_OPTIONS_PATH = os.getenv("FILTER_OPTIONS_PATH")

# config
similarity_score_threshold = 0.2
max_context_records = 20
min_records_for_summarisation = 5

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


@st.cache_resource()
def load_filter_dropdown_values(path_to_json):
    with open(path_to_json, "r") as file:
        data = json.load(file)
    return data


client = load_qdrant_client(6333)
model = load_model("all-mpnet-base-v2")
filter_options = load_filter_dropdown_values(FILTER_OPTIONS_PATH)


def main():
    # Sidebar
    st.sidebar.header("Settings")
    st.sidebar.write(
        "This dashboard uses a large language model to perform semantic search and return the most relevant feedback records."
    )

    # Main content area
    st.title("Feedback AI Streamlit Dashboard Prototype")
    st.subheader("Semantic Search of Feedback")

    # Setting k -> inf as placeholder
    k = 1000000

    # Free text box for one search term
    search_term_input = st.sidebar.text_input(
        "Enter a search term or phrase: \n (e.g. tax, Universal Credit, driving licence)"
    )
    search_terms = search_term_input.strip().lower()

    # Free text box for comma-separated list of subject pages.
    # page_path_input = st.sidebar.text_input(
    #     "Enter optional subject page paths comma-separated: \n (e.g. /renew-medical-driving-licence)"
    # )
    # page_paths = (
    #     [item.strip() for item in page_path_input.split(",")] if page_path_input else ["/"]
    # )

    matched_page_paths = st.sidebar.multiselect(
        "Select path:", filter_options["page_paths"], max_selections=4, default=[]
    )

    urgency_input = st.sidebar.multiselect(
        "Select urgency (Low:1, High:3, Unknown:-1):",
        ["1", "2", "3", "-1"],
        max_selections=4,
    )

    org_input = st.sidebar.multiselect(
        "Select organisation (type to search):", filter_options["orgs"], default=[]
    )

    doc_type_input = st.sidebar.multiselect(
        "Select document type (type to search):",
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
        "subject_page_path": matched_page_paths,
        "urgency": urgency_input,
        "organisation": org_input,
        "document_type": doc_type_input,
    }

    if st.sidebar.button("Apply Filters"):
        if search_term_input:
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
                if (
                    output["similarity_score"] > similarity_score_threshold
                    and start_date <= output["created_date"] <= end_date
                ):
                    filtered_list.append(output)

            st.write(f"{len(filtered_list)} relevant feedback records found...")

            # Topic summary where > n records returned
            # limiting to 20 records for context, to avoid token limits

            if len(filtered_list) > min_records_for_summarisation:
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
                    "Insufficient records for summarisation. Please select a larger date range or different search term."
                )
            st.write("------")
            st.write("Most relevant feedback records:")
            st.dataframe(filtered_list)
    else:
        st.write(
            "Please supply a search term or terms and hit Apply Filters to see results..."
        )


if __name__ == "__main__":
    main()
