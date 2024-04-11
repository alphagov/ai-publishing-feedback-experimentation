from dotenv import load_dotenv
import os
import pickle
import streamlit as st
import plotly.graph_objs as go
from collections import defaultdict
import numpy as np

load_dotenv()

QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_PORT = os.getenv("QDRANT_PORT")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
HF_MODEL_NAME = os.getenv("HF_MODEL_NAME")
PUBLISHING_PROJECT_ID = os.getenv("PUBLISHING_PROJECT_ID")
EVALUATION_TABLE = os.getenv("EVALUATION_TABLE")
EVALUATION_TABLE = f"`{EVALUATION_TABLE}`"


# config = load_config(".config/config.json")
# similarity_threshold = float(config.get("similarity_threshold_1"))

with open("data/regex_ids.pkl", "rb") as f:
    regex_ids = pickle.load(f)

with open("data/precision_values.pkl", "rb") as f:
    precision_values = pickle.load(f)

with open("data/recall_values.pkl", "rb") as f:
    recall_values = pickle.load(f)

# client = load_qdrant_client(QDRANT_HOST, port=QDRANT_PORT)
# model = load_model(HF_MODEL_NAME)

# model = load_model(HF_MODEL_NAME)

# data = get_data_for_evaluation(
#     project_id=PUBLISHING_PROJECT_ID,
#     evaluation_table=EVALUATION_TABLE,
# )

# # Get unique labels
# unique_labels = get_unique_labels(data)


# def calculate_metrics(unique_label, regex_ids, model, client, similarity_threshold):
#     # Get the count of records from the regex counts
#     relevant_records = regex_ids[unique_label]

#     # Embed the label
#     query_embedding = model.encode(unique_label)

#     # Retrieve the top K results for the label
#     try:
#         results = get_semantically_similar_results(
#             client=client,
#             collection_name=COLLECTION_NAME,
#             query_embedding=query_embedding,
#             score_threshold=similarity_threshold,
#         )
#         result_ids = [str(result.id) for result in results]
#     except Exception as e:
#         print(f"get_semantically_similar_results error: {e}")
#         pass

#     # Calculate precision and recall
#     precision = calculate_precision(result_ids, relevant_records)
#     recall = calculate_recall(result_ids, relevant_records)

#     return precision, recall


# # Loop over unique labels and similarity thresholds
# precision_values = []
# recall_values = []
# for unique_label in unique_labels[:100]:
#     for threshold in np.arange(0, 1.1, 0.1):
#         precision, recall = calculate_metrics(
#             unique_label=unique_label,
#             regex_ids=regex_ids,
#             model=model,
#             client=client,
#             similarity_threshold=threshold,
#         )
#         precision_values.append({unique_label: {threshold: precision}})
#         recall_values.append({unique_label: {threshold: recall}})


def calculate_mean_values(data_list):
    # Dictionary to hold cumulative sums and counts for each test
    sums_counts = defaultdict(lambda: {"sum": 0, "count": 0})

    for item in data_list:
        for _, values in item.items():
            for threshold, value in values.items():
                sums_counts[threshold]["sum"] += value
                sums_counts[threshold]["count"] += 1

    # Calculate mean for each test
    mean_values = {
        test: info["sum"] / info["count"] for test, info in sums_counts.items()
    }
    return mean_values


boxplot_precision_values = [list(item.values())[0] for item in precision_values]
rounded_boxplot_precision_values = [
    {round(key, 2): value for key, value in item.items()} for item in precision_values
]
boxplot_recall_values = [list(item.values())[0] for item in recall_values]
rounded_boxplot_recall_values = [
    {round(key, 2): value for key, value in item.items()} for item in recall_values
]


def get_threshold_values(data, input_threshold=0.0):
    threshold_list = []
    for item in data:
        for threshold, value in item.items():
            if threshold == input_threshold:
                threshold_list.append(value)
    return threshold_list


box_precision_plotting_values = {}

for i in np.arange(0, 1.1, 0.1):
    threshold_list = get_threshold_values(
        rounded_boxplot_precision_values,
        input_threshold=i,
    )
    box_precision_plotting_values[i] = threshold_list

box_recall_plotting_values = {}

for i in np.arange(0, 1.1, 0.1):
    threshold_list = get_threshold_values(
        rounded_boxplot_recall_values,
        input_threshold=i,
    )
    box_recall_plotting_values[i] = threshold_list

# Calculate and print the mean values
mean_precision_values = calculate_mean_values(precision_values)
mean_recall_values = calculate_mean_values(recall_values)

# Round the keys and values to 2 decimal places
mean_precision_values = {
    round(k, 2): round(v, 2) for k, v in mean_precision_values.items()
}
mean_recall_values = {round(k, 2): round(v, 2) for k, v in mean_recall_values.items()}


# Streamlit app
def main():
    st.title("Precision and Recall Calculator")

    # Streamlit slider for selecting threshold
    selected_threshold = st.slider(
        "Select Threshold", min_value=0.0, max_value=1.0, step=0.1
    )

    thresholds = list(mean_precision_values.keys())
    precision_scores = list(mean_precision_values.values())
    recall_scores = list(mean_recall_values.values())

    # Find the precision score for the selected threshold
    selected_precision_index = thresholds.index(selected_threshold)
    selected_precision = precision_scores[selected_precision_index]
    selected_recall = recall_scores[selected_precision_index]

    # Display the selected precision score
    st.write(f"Precision Score: {selected_precision}")
    st.write(f"Recall Score: {selected_recall}")

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
    fig2.add_trace(
        go.Box(
            y=list(box_precision_plotting_values.values()),
            x=list(box_precision_plotting_values.keys()),
            name="Precision",
        )
    )

    # Add box plot for recall scores

    fig2.add_trace(
        go.Box(
            y=list(box_recall_plotting_values.values()),
            x=list(box_recall_plotting_values.keys()),
            name="Recall",
        )
    )

    # Update layout to add titles and make it clearer
    fig2.update_layout(
        title="Threshold vs. Precision/Recall Score",
        xaxis_title="Threshold",
        yaxis_title="Precision/Recall Score",
    )

    # Show the plot
    st.plotly_chart(fig2)


if __name__ == "__main__":
    main()
