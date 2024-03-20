keys_to_extract = [
    "created",
    "feedback",
    "url",
    "page_title",
    "urgency",
    "feedback_type",
    "primary_department",
    "document_type",
    # "department",
    # "publishing_app",
    # "locale",
    # "sentiment",
    # "spam_classification",
    # "labels",
]

renaming_dict = {
    "created": "Date",
    "feedback": "Feedback comment",
    "url": "URL",
    "page_title": "Page title",
    "urgency": "Urgency",
    "feedback_type": "Feedback type",
    "primary_department": "Publishing department",
    "document_type": "Content type",
    # "department": "Department",
    # "publishing_app": "Publishing app",
    # "locale": "Locale",
    # "sentiment": "Sentiment",
    # "spam_classification": "Spam classification",
    # "labels": "Labels",
}

urgency_translate = {"Low": "1", "Medium": "2", "High": "3", "Unknown": "-1"}
