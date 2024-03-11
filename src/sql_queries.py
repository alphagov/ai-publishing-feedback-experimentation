query_labelled_feedback = """

SELECT
    feedback.type,
    DATE(feedback.created) AS created,
    feedback.subject_page_path,
    CONCAT('https://www.gov.uk', feedback.subject_page_path) AS reconstructed_path,
    CAST(feedback.feedback_record_id AS STRING) AS feedback_record_id,
    feedback.response_value,
    feedback.organisation,
    feedback.document_type,
    feedback.embeddings,
    feedback.sentiment,
    feedback.spam_classification,
    feedback.spam_probability,
    labels.labels,
    labels.urgency
FROM @PUBLISHING_VIEW feedback
JOIN @labelled_feedback_table labels
  ON CAST(feedback.feedback_record_id AS INT)=CAST(labels.id AS INT)
WHERE feedback.created > DATE("2023-08-01")
AND document_type != "special route"
LIMIT 1500
"""
