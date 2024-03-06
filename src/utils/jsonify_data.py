import json


def jsonify_data(records: list, labelled=False):
    """
    Create json string from feedback
    :return: json string of feedback records
    """
    subs = []
    for i, item in enumerate(records):
        response_value = item["concatenated_response_value"]
        subs.append(
            {
                "id": item["feedback_record_id"],
                "feedback": response_value,
                "label": [item["labels"] if labelled else ""],
            }
        )

    return json.dumps(subs, indent=4)
