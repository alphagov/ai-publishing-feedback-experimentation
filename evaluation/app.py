from dotenv import load_dotenv
import os
import pickle
import streamlit as st
import subprocess
import plotly.graph_objs as go
from src.collection.evaluate_collection import (
    create_precision_boxplot_data,
    create_recall_boxplot_data,
    create_precision_line_data,
    create_recall_line_data,
)

load_dotenv()

QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_PORT = os.getenv("QDRANT_PORT")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
HF_MODEL_NAME = os.getenv("HF_MODEL_NAME")
PUBLISHING_PROJECT_ID = os.getenv("PUBLISHING_PROJECT_ID")
EVALUATION_TABLE = os.getenv("EVALUATION_TABLE")
EVALUATION_TABLE = f"`{EVALUATION_TABLE}`"

# Check if the pickle files exist
if (
    not os.path.exists("data/regex_ids.pkl")
    or not os.path.exists("data/precision_values.pkl")
    or not os.path.exists("data/recall_values.pkl")
):
    # run the evaluation/create_eval_json.py script
    print("Running evaluation/create_eval_json.py ...")
    subprocess.run(
        ["python", "evaluation/create_eval_json.py", "--save_outputs", "True"]
    )

# Load the data
with open("data/regex_ids.pkl", "rb") as f:
    regex_ids = pickle.load(f)

with open("data/precision_values.pkl", "rb") as f:
    precision_values = pickle.load(f)

with open("data/recall_values.pkl", "rb") as f:
    recall_values = pickle.load(f)


precision_boxplot_data = create_precision_boxplot_data(precision_values)
recall_boxplot_data = create_recall_boxplot_data(recall_values)
precision_line_data = create_precision_line_data(precision_values)
recall_line_data = create_recall_line_data(recall_values)


# Streamlit app
def main():
    st.title("Precision and Recall Calculator")

    # Streamlit slider for selecting threshold
    selected_threshold = st.slider(
        "Select Threshold", min_value=0.0, max_value=1.0, step=0.1
    )

    thresholds = list(precision_line_data.keys())
    precision_scores = list(precision_line_data.values())
    recall_scores = list(recall_line_data.values())

    # Find the precision score for the selected threshold
    selected_precision_index = thresholds.index(selected_threshold)
    selected_precision = precision_scores[selected_precision_index]
    selected_recall = recall_scores[selected_precision_index]

    # Display the selected precision score
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Precision Score", selected_precision)
    with col2:
        st.metric("Recall Score", selected_recall)
    with col3:
        st.metric("F2 score placeholder", 0)

    # Plot
    fig = go.Figure()

    # Add line plot for thresholds vs. precision scores
    fig.add_trace(
        go.Scatter(x=thresholds, y=precision_scores, mode="lines", name="Precision")
    )
    fig.add_trace(
        go.Scatter(x=thresholds, y=recall_scores, mode="lines", name="Recall")
    )

    # Add a point to highlight the selected threshold and precision score
    fig.add_trace(
        go.Scatter(
            x=[selected_threshold],
            y=[selected_precision],
            mode="markers",
            marker=dict(color="red", size=10),
            name="Selected",
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
        )
    )

    # Update layout to add titles and make it clearer
    fig.update_layout(
        title="Threshold vs. Precision/Recall Score",
        xaxis_title="Threshold",
        yaxis_title="Precision/Recall Score",
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
