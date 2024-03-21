import datetime
import os
import json

import streamlit as st
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

from src.collection.query_collection import (
    get_semantically_similar_results,
    filter_search,
)
from src.common import urgency_translate, renaming_dict
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

st.set_page_config(layout="wide")


# Load the model only once, at the start of the app.
# TODO: Replace with call to HF Inferece API or OpenAI API
@st.cache_resource()
def load_qdrant_client():
    client = QdrantClient(QDRANT_HOST, port=QDRANT_PORT)
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


@st.cache_resource()
def read_html_file(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


@st.cache_resource()
def load_config(config_file_path):
    with open(config_file_path, "r") as file:
        config = json.load(file)
    return config


client = load_qdrant_client()
model = load_model(HF_MODEL_NAME)
filter_options = load_filter_dropdown_values(FILTER_OPTIONS_PATH)

config = load_config(".config/config.json")
similarity_threshold = config.get("dot_product_threshold_1")
max_context_records = config.get("dot_product_threshold_1")
min_records_for_summarisation = config.get("min_records_for_summarisation")


def main():
    # Create a container for the banner
    with st.container():
        # Use markdown with inline CSS/HTML

        # html_content = read_html_file('app/banner.html')
        # st.markdown(html_content, unsafe_allow_html=True)
        with open("app/banner.html", "r", encoding="utf-8") as file:
            html_content = file.read()
            st.markdown(html_content, unsafe_allow_html=True)

    # Main content area
    st.header("Explore user feedback")
    st.write(
        "Explore user feedback comments, including themes across topics and pages. \
             This tool brings together feedback from users submitted via the \
             'report a problem on this page' link and smart survey responses."
    )

    # Sidebar
    st.sidebar.image("data/govuk-feedback.png")
    st.sidebar.header("Explore themes in user feedback\n")

    st.sidebar.write(
        "Explore user feedback by topic, URL, urgency rathing, content type  and/or organisation, using AI to summarise themes\n"
    )

    st.sidebar.subheader("AI summarisation")

    get_summary = st.sidebar.checkbox(
        "Summarise relevant feedback",
        value=True,
    )

    st.sidebar.subheader("Set date range (optional)")

    # Date range slider in the sidebar.
    today = datetime.date.today()

    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input(
            "Start date:", today - datetime.timedelta(days=90), format="DD/MM/YYYY"
        )
    with col2:
        end_date = st.date_input("End date:", today, format="DD/MM/YYYY")

    st.sidebar.divider()

    # Free text box for one search term
    st.sidebar.header("Explore by topic")
    search_term_input = st.sidebar.text_input(
        "Enter a keyword or phrase.\n For example, tax, driving licence, Universal Credit"
    )

    semantic_search_button = st.sidebar.button("Explore feedback by topic")

    search_terms = search_term_input.strip().lower()

    st.sidebar.divider()

    st.sidebar.header("Narrow your search\n")

    st.sidebar.subheader("By URL(s)")

    # List of all pages for dropdown and filtering
    all_pages = filter_options["subject_page_path"]

    user_input_pages = st.sidebar.multiselect(
        "Start typing and select the URL from dropdown\nFor example, /vat-rate or /browse/tax",
        all_pages,
        # max_selections=4,
        default=[],
    )
    # File upload for list of URLs
    uploaded_url_file = st.sidebar.file_uploader(
        "Or bulk upload a list of URLs using a CSV or TXT file. Mac file limit 200MB per file",
        type=["txt", "csv"],
    )

    include_child_pages = True

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
        matched_page_paths = [
            url
            for url in all_pages
            if url and any(url.startswith(path) for path in user_input_pages)
        ]
    elif not include_child_pages:
        matched_page_paths = user_input_pages
    else:
        matched_page_paths = []

    st.sidebar.subheader("By urgency")

    urgency_user_input = st.sidebar.multiselect(
        "See feedback by high, medium, low and unknown urgency rating.\nUrgency has been inferred by AI.",
        ["Low", "Medium", "High", "Unknown"],
        max_selections=4,
    )

    # translate urgency rating to human readable
    urgency_input = [urgency_translate[value] for value in urgency_user_input]

    st.sidebar.subheader("By publishing organisation")
    org_input = st.sidebar.multiselect(
        "Select publishing organisation:", filter_options["organisation"], default=[]
    )

    st.sidebar.subheader("By content type")
    doc_type_input = st.sidebar.multiselect(
        "Select content type:",
        filter_options["document_type"],
        default=[],
    )

    filter_search_button = st.sidebar.button("Explore feedback")

    st.sidebar.divider()

    st.sidebar.write(
        "Similarity score is calculated by an AI model. \
                     The higher the score, the more similar the feedback \
                     content is to the search term or phrase."
    )
    # convert to int if not None, else keep as None
    urgency_input = [int(urgency) if urgency else None for urgency in urgency_input]

    filter_dict = {
        "url": matched_page_paths,
        "urgency": urgency_input,
        "primary_department": org_input,
        "document_type": doc_type_input,
    }

    if any([filter_search_button, semantic_search_button]):
        if len(search_term_input) > 0:
            query_embedding = model.encode(search_terms)
            # Call the search function with filters
            search_results = get_semantically_similar_results(
                client=client,
                collection_name=COLLECTION_NAME,
                query_embedding=query_embedding,
                score_threshold=similarity_threshold,
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
                if key in renaming_dict:
                    for (
                        key,
                        value,
                    ) in (
                        renaming_dict.items()
                    ):  # Check if the key exists in keys_to_extract
                        result[value] = payload[key]

            result_ordered = {key: result[key] for key in renaming_dict.values()}
            result_ordered["Similarity score"] = (
                result["score"] if "score" in result else float(1)
            )
            # result_ordered["payload"] = payload

            result_ordered["created_date"] = datetime.datetime.strptime(
                result_ordered[renaming_dict["created"]], "%Y-%m-%d"
            ).date()

            # Filter on date
            if (
                result_ordered["Similarity score"] > similarity_threshold
                and start_date <= result_ordered["created_date"] <= end_date
            ):
                result_ordered.pop("created_date")
                filtered_list.append(result_ordered)

        st.write(
            f"{len(filtered_list)} relevant feedback comments found for your search:"
        )

        # Topic summary where > n records returned
        # limiting to 20 records for context, to avoid token limits

        if get_summary and len(filtered_list) > min_records_for_summarisation:
            feedback_for_context = [
                record[renaming_dict["feedback"]] for record in filtered_list
            ]
            summary = create_openai_summary(
                system_prompt,
                user_prompt,
                feedback_for_context[:max_context_records],
                OPENAI_API_KEY,
            )
            st.subheader(
                f"Top themes based on {len(feedback_for_context)} records of user feedback"
            )
            st.write(
                "Identified and summarised by AI technology. Please verify the outputs with other data sources to ensure accuracy of information."
            )
            st.write(summary["open_summary"])
        elif get_summary and len(filtered_list) <= min_records_for_summarisation:
            st.write(
                "There's not enough feedback matching your search criteria to identify top themes.\n\
                Try searching with fewer criteria or across more URLs to increase the likelihood of results."
            )
        elif not get_summary and len(filtered_list) > min_records_for_summarisation:
            st.write(
                "No summary requested. Check box to get an AI-generated summary of relevant feedback."
            )
        else:
            st.write(
                "No summary requested. Insufficient feedback records for summarisation."
            )
        st.subheader("All user feedback comments based on your search criteria")
        st.dataframe(
            filtered_list,
            column_config={
                "Date": st.column_config.DateColumn(
                    "Date",
                    format="DD/MM/YYYY",
                ),
            },
        )


if __name__ == "__main__":
    main()
