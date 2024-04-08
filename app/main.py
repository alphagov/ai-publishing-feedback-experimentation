import datetime
import json
import os
import subprocess

import streamlit as st
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from streamlit_js_eval import streamlit_js_eval

from prompts.openai_summarise import system_prompt, user_prompt
from src.collection_utils.query_collection import (
    filter_search,
    get_semantically_similar_results,
)
from src.common import renaming_dict, urgency_translate
from src.utils.call_openai_summarise import create_openai_summary
from src.utils.utils import process_csv_file, process_txt_file

# get env vars
load_dotenv()
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
FILTER_OPTIONS_PATH = os.getenv("FILTER_OPTIONS_PATH")
HF_MODEL_NAME = os.getenv("HF_MODEL_NAME")
QDRANT_HOST = os.getenv("QDRANT_HOST")  # "localhost" if running locally
QDRANT_PORT = os.getenv("QDRANT_PORT")

st.set_page_config(
    layout="wide",
    menu_items={
        "Report a bug": "https://forms.gle/C7P6kYrRJT4F5yfz8",
        "About": "This is a prototype app developed by the GOV.UK AI team. \
                    For assistance, please contact the team via Slack at #ai-govuk.",
    },
)


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


@st.cache_resource()
def get_filters_metadata():
    try:
        subprocess.run(["python", "-u", "app/get_metadata_for_filters.py"])
    except Exception as e:
        print(f"Error running metadata script: {e}")


client = load_qdrant_client()
model = load_model(HF_MODEL_NAME)

config = load_config(".config/config.json")
similarity_threshold = float(config.get("similarity_threshold_1"))
max_context_records = int(config.get("max_records_for_summarisation"))
min_records_for_summarisation = int(config.get("min_records_for_summarisation"))

print(f"Using similarity threshold: {similarity_threshold}")

# Run the script to get metadata for filters
get_filters_metadata()
filter_options = load_filter_dropdown_values(FILTER_OPTIONS_PATH)


def main():
    # Apply custom css elements
    with open("app/style/custom.css", "r") as file:
        st.sidebar.markdown(f"<style>{file.read()}</style>", unsafe_allow_html=True)

    sidebar_image_path = "app/style/govuk-feedback-prototype-sidebar.png"
    # Create a container for the banner
    with st.container():
        # Use markdown with inline CSS/HTML
        with open("app/style/banner.html", "r", encoding="utf-8") as file:
            html_content = file.read()
            st.markdown(html_content, unsafe_allow_html=True)

    # Main content area
    st.header("Explore user feedback")
    st.write(
        "Explore user feedback comments, including themes across topics and pages. \
             This tool brings together feedback from users submitted via the \
             'report a problem on this page' link and smart survey responses."
    )
    st.text("")

    # Sidebar
    st.sidebar.image(sidebar_image_path, use_column_width=True)
    st.sidebar.header("Explore themes in user feedback\n")

    st.sidebar.write(
        "Search by keyword, URL(s), urgency, organisation and/or content type. Use AI summarisation to identify themes in user comments."
    )

    st.sidebar.subheader("AI summarisation")

    left, right = st.sidebar.columns(2)
    with left:
        get_summary = st.checkbox(
            "Summarise relevant feedback",
            value=False,
            key="get_summary",
        )
    with right:
        remove_spam = st.checkbox(
            "Include comments marked as spam",
            value=False,
            key="remove_spam",
        )

    st.sidebar.subheader("Set date range (optional)")

    # Date range slider in the sidebar.
    today = datetime.date.today()
    n_days_default = 90
    st.sidebar.write(f"Showing data from past {n_days_default} days as default view.")

    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input(
            "Start date:",
            today - datetime.timedelta(days=n_days_default),
            format="DD/MM/YYYY",
        )
    with col2:
        end_date = st.date_input("End date:", today, format="DD/MM/YYYY")

    st.sidebar.divider()

    # Free text box for one search term
    st.sidebar.header("Explore by keyword or phrase\n")
    search_term_input = st.sidebar.text_input(
        "For example, tax, driving licence, Universal Credit", key="search_term_input"
    )

    search_terms = search_term_input.strip().lower()

    st.sidebar.header("By URL(s)")

    # List of all pages for dropdown and filtering
    all_pages = filter_options["subject_page_path"]

    user_input_pages = st.sidebar.multiselect(
        "Start typing and select the URL from dropdown\nFor example, /vat-rate or /browse/tax",
        all_pages,
        # max_selections=4,
        default=[],
        key="user_input_pages",
    )
    # File upload for list of URLs
    uploaded_url_file = st.sidebar.file_uploader(
        "Or bulk upload a list of URLs using a CSV or TXT file. Mac file limit 200MB per file",
        type=["txt", "csv"],
        key="uploaded_url_file",
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

    st.sidebar.divider()
    st.sidebar.header("Narrow your search\n")
    st.sidebar.subheader("By urgency")

    urgency_user_input = st.sidebar.multiselect(
        "See feedback by high, medium, low and unknown urgency rating (Urgency inferred by AI).",
        ["Low", "Medium", "High", "Unknown"],
        max_selections=4,
        key="urgency_user_input",
    )

    # translate urgency rating to human readable
    urgency_input = [urgency_translate[value] for value in urgency_user_input]

    st.sidebar.subheader("By publishing organisation")
    org_input = st.sidebar.multiselect(
        "Select publishing organisation:",
        filter_options["organisation"],
        default=[],
        key="org_input",
    )

    st.sidebar.subheader("By content type")
    doc_type_input = st.sidebar.multiselect(
        "For example, guide, detailed guide, consultation",
        filter_options["document_type"],
        default=[],
        key="doc_type_input",
    )

    # Add buttons to search and clear filters
    st.sidebar.text("")
    search_button = st.sidebar.button(
        "Explore feedback",
        key="search_button",
        type="primary",
        help="Click to search",
        use_container_width=True,
    )

    clear_filters = st.sidebar.button(
        "Clear all filters",
        key="clear_filters",
        type="secondary",
        help="Reset search parameters",
        use_container_width=True,
    )

    if clear_filters:
        # Reload webpage to clear all filters
        streamlit_js_eval(js_expressions="parent.window.location.reload()")

    st.sidebar.divider()

    st.sidebar.markdown(
        "_**Similarity score** is calculated by an AI model. \
                     The higher the score, the more similar the feedback \
                     content is to the search term or phrase._"
    )

    st.sidebar.markdown(
        "_**Urgency** is inferred by an AI model via the OpenAI API. \
                     It should reflect the urgency of the problem from \
                     the point of view of the publishing organisation._"
    )
    # convert to int if not None, else keep as None
    urgency_input = [int(urgency) if urgency else None for urgency in urgency_input]

    spam_filter = ["not spam"] if remove_spam else ["spam", "not spam", ""]

    filter_dict = {
        "url": matched_page_paths,
        "urgency": urgency_input,
        "primary_department": org_input,
        "document_type": doc_type_input,
        "spam_classification": spam_filter,
    }

    if search_button:
        if len(search_term_input) > 0:
            query_embedding = model.encode(search_terms)
            # Call the search function with filters
            print(f"Running semantic search on {COLLECTION_NAME}...")
            search_results = get_semantically_similar_results(
                client=client,
                collection_name=COLLECTION_NAME,
                query_embedding=query_embedding,
                score_threshold=similarity_threshold,
                filter_dict=filter_dict,
            )
            results = [dict(result) for result in search_results]
            print(f"Num results: {len(results)}")
        elif (
            len(search_term_input) == 0
            and any(len(filter_dict[key]) > 0 for key in ["url", "primary_department"])
            > 0
        ):
            st.write("Running filter search...")
            # Call the filter function
            search_results = filter_search(
                client=client, collection_name=COLLECTION_NAME, filter_dict=filter_dict
            )
            data, _ = search_results
            results = [dict(result) for result in data]
        else:
            st.write(
                "Please supply a search term or URL(s) and hit 'Explore Feedback' to see results..."
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

            result_ordered["created_date"] = datetime.datetime.strptime(
                result_ordered[renaming_dict["created"]], "%Y-%m-%d"
            ).date()

            # Reformat urgency to human readable
            inverted_urgency_translate = {v: k for k, v in urgency_translate.items()}
            numeric_urgency = str(result_ordered["Urgency"])
            if numeric_urgency in inverted_urgency_translate:
                result_ordered["Urgency"] = inverted_urgency_translate[numeric_urgency]

            # Filter on date
            if (
                result_ordered["Similarity score"] > similarity_threshold
                and start_date <= result_ordered["created_date"] <= end_date
            ):
                result_ordered.pop("created_date")
                filtered_list.append(result_ordered)

            # Reformat similarity score as percentage, to no decimal places
            result_ordered[
                "Similarity score"
            ] = f"{result_ordered['Similarity score']*100:.0f}%"

        # Topic summary where > n records returned
        if get_summary and len(filtered_list) > min_records_for_summarisation:
            available_feedback_for_context = [
                record[renaming_dict["feedback"]] for record in filtered_list
            ]
            # Limit the number of feedback records to summarise, if number exceeds max_context_records
            num_feedback_for_context = (
                len(available_feedback_for_context)
                if len(available_feedback_for_context) <= max_context_records
                else max_context_records
            )
            summary = create_openai_summary(
                system_prompt,
                user_prompt,
                available_feedback_for_context[:num_feedback_for_context],
                OPENAI_API_KEY,
            )
            st.subheader(
                f"Top themes based on {num_feedback_for_context} records of user feedback"
            )
            st.write(
                "Identified and summarised by AI technology. Please verify the outputs with other data sources to ensure accuracy of information."
            )
            st.write(summary["open_summary"])
            st.text("")
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
        st.subheader(
            f"{len(filtered_list)} user feedback comments based on your search criteria"
        )
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
