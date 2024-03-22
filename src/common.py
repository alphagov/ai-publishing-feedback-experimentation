keys_to_extract = [
    "created",
    "feedback",
    "url",
    "page_title",
    "urgency",
    "feedback_type",
    "primary_department",
    "document_type",
    "spam_classification",
    # "department",
    # "publishing_app",
    # "locale",
    # "sentiment",
]

renaming_dict = {
    "created": "Date",
    "feedback": "Feedback comment",
    "feedback_full": "Feedback comment with associated comments",
    "url": "URL",
    "page_title": "Page title",
    "urgency": "Urgency",
    "feedback_type": "Feedback type",
    "primary_department": "Publishing department",
    "document_type": "Content type",
    "spam_classification": "Spam classification",
    # "department": "Department",
    # "publishing_app": "Publishing app",
    # "locale": "Locale",
    # "sentiment": "Sentiment",
}

urgency_translate = {"Low": "1", "Medium": "2", "High": "3", "Unknown": "-1"}
