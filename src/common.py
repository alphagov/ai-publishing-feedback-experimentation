keys_to_extract = [
    "feedback_record_id",
    "created",
    "score",
    "response_value",
    "subject_page_path",
    "organisation",
    "document_type",
    "type",
    "urgency",
    "sentiment",
]

rename_dictionary = {
    "created_date": "created_date",
    "response_value": "feedback",
    "subject_page_path": "url",
    "score": "similarity_score",
    "organisation": "department",
    "document_type": "document_type",
    "type": "feedback_type",
    "urgency": "urgency",
    "sentiment": "sentiment",
    "labels": "topics",
}
