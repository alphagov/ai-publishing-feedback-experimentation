from dotenv import load_dotenv
import os
import pickle
import streamlit as st
import subprocess
import plotly.graph_objs as go
from src.collection_utils.evaluate_collection import (
    create_precision_boxplot_data,
    create_recall_boxplot_data,
    create_precision_line_data,
    create_recall_line_data,
)

load_dotenv()

QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_PORT = os.getenv("QDRANT_PORT")
COLLECTION_NAME = os.getenv("EVAL_COLLECTION_NAME")
HF_MODEL_NAME = os.getenv("HF_MODEL_NAME")
PUBLISHING_PROJECT_ID = os.getenv("PUBLISHING_PROJECT_ID")
EVALUATION_TABLE = os.getenv("EVALUATION_TABLE")
EVALUATION_TABLE = f"`{EVALUATION_TABLE}`"


# Check if the pickle files exist via a cached function
def check_pickle_files():
    data_path = "data"
    required_files = [
        "regex_ids.pkl",
        "precision_values.pkl",
        "recall_values.pkl",
        "f2_scores.pkl",
    ]
    files_exist = os.path.isdir(data_path) and all(
        os.path.exists(os.path.join(data_path, file)) for file in required_files
    )
    return files_exist


# Create the pickle files (no caching so it checks every time)
def create_files():
    print("Running evaluation/create_eval_json.py ...")
    subprocess.run(
        ["python", "evaluation/create_eval_json.py", "--save_outputs", "True"]
    )


# Check if the pickle files exists
if not check_pickle_files():
    create_files()


# Load the pickle files via a cached function
@st.cache_data
def load_pickle_data(file_path):
    with open(file_path, "rb") as file:
        data = pickle.load(file)
    return data


# Load the pickle files
# TODO: can I parameterise the list of files so I don't type here and in the check_pickle_files function?
regex_ids = load_pickle_data("data/regex_ids.pkl")  # TODO: Do I need this?
recall_values = load_pickle_data("data/recall_values.pkl")
precision_values = load_pickle_data("data/precision_values.pkl")
f2scores = load_pickle_data("data/f2_scores.pkl")

# Create the data for the box plots and line plots
precision_boxplot_data = create_precision_boxplot_data(precision_values)
recall_boxplot_data = create_recall_boxplot_data(recall_values)
precision_line_data = create_precision_line_data(precision_values)
recall_line_data = create_recall_line_data(recall_values)
f2scores_line_data = create_recall_line_data(f2scores)


# Streamlit app
def main():
    st.title("Precision and Recall Calculator")

    # Streamlit slider for selecting threshold
    selected_threshold = st.slider(
        "Select Threshold", min_value=0.0, max_value=1.0, step=0.1
    )

    # Get the precision, recall, and f2 scores as lists
    thresholds = list(precision_line_data.keys())
    precision_scores = list(precision_line_data.values())
    recall_scores = list(recall_line_data.values())
    f2scores = list(f2scores_line_data.values())

    # Index the score lists for the selected threshold
    selected_index = thresholds.index(selected_threshold)
    selected_precision = precision_scores[selected_index]
    selected_recall = recall_scores[selected_index]
    selected_f2 = f2scores[selected_index]

    # Display the selected scores as metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Precision Score", selected_precision)
    with col2:
        st.metric("Recall Score", selected_recall)
    with col3:
        st.metric("F2 score", selected_f2)

    # Plot
    fig = go.Figure()

    # Add line plot traces for thresholds vs. scores
    fig.add_trace(
        go.Scatter(x=thresholds, y=precision_scores, mode="lines", name="Precision")
    )
    fig.add_trace(
        go.Scatter(x=thresholds, y=recall_scores, mode="lines", name="Recall")
    )
    fig.add_trace(go.Scatter(x=thresholds, y=f2scores, mode="lines", name="F2 score"))

    # Add a point to highlight the selected threshold and precision score
    fig.add_trace(
        go.Scatter(
            x=[selected_threshold],
            y=[selected_precision],
            mode="markers",
            marker=dict(color="red", size=10),
            name="Selected",
            showlegend=False,
        )
    )

    # Add a point to highlight the selected threshold and recall score
    fig.add_trace(
        go.Scatter(
            x=[selected_threshold],
            y=[selected_recall],
            mode="markers",
            marker=dict(color="blue", size=10),
            name="Selected",
            showlegend=False,
        )
    )

    # Add a point to highlight the selected threshold and f2 score
    fig.add_trace(
        go.Scatter(
            x=[selected_threshold],
            y=[selected_f2],
            mode="markers",
            marker=dict(color="green", size=10),
            name="Selected",
            showlegend=False,
        )
    )

    # Update layout to add titles and make it clearer
    fig.update_layout(
        title="Threshold vs. Precision/Recall/F2 Score",
        xaxis_title="Threshold",
        yaxis_title="Precision/Recall/F2 Score",
    )

    # Show the plot
    st.plotly_chart(fig)

    # Box plot
    fig2 = go.Figure()

    # Add box plot for precision scores
    for item in precision_boxplot_data.items():
        if item[0] == selected_threshold:
            fig2.add_trace(
                go.Box(
                    y=item[1],
                    name=f"Threshold: {item[0]}",
                    marker=dict(color="#00cc96", opacity=1),
                )
            )
        else:
            fig2.add_trace(
                go.Box(
                    y=item[1],
                    name=f"Threshold: {item[0]}",
                    marker=dict(color="#19d3f3", opacity=0.5),
                )
            )
    # Update layout to add titles and make it clearer
    fig2.update_layout(
        title="Threshold vs. Precision Score",
        # xaxis_title="Threshold",
        yaxis_title="Precision Score",
    )

    # Hide the legend
    fig2.update_layout(showlegend=False)

    # Show the plot
    st.plotly_chart(fig2)

    # Box plot
    fig3 = go.Figure()

    # Add box plot for recall scores
    for item in recall_boxplot_data.items():
        if item[0] == selected_threshold:
            fig3.add_trace(
                go.Box(
                    y=item[1],
                    name=f"Threshold: {item[0]}",
                    marker=dict(color="#00cc96", opacity=1),
                )
            )
        else:
            fig3.add_trace(
                go.Box(
                    y=item[1],
                    name=f"Threshold: {item[0]}",
                    marker=dict(color="#19d3f3", opacity=0.5),
                )
            )

    # Update layout to add titles and make it clearer
    fig3.update_layout(
        title="Threshold vs. Recall Score",
        # xaxis_title="Threshold",
        yaxis_title="Recall Score",
    )

    # Hide the legend
    fig3.update_layout(showlegend=False)

    # Show the plot
    st.plotly_chart(fig3)


if __name__ == "__main__":
    main()
