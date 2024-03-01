query_labelled_feedback = """

SELECT
    feedback.type,
    feedback.created,
    feedback.subject_page_path,
    CONCAT('https://www.gov.uk', feedback.subject_page_path) AS reconstructed_path,
    feedback.feedback_record_id,
    feedback.response_value,
    feedback.embeddings,
    feedback.sentiment,
    feedback.spam_classification,
    feedback.spam_probability,
    labels.labels,
    labels.urgency
FROM @PUBLISHING_VIEW feedback
JOIN @labelled_feedback_table labels
  ON feedback.feedback_record_id=labels.id
WHERE feedback.created > DATE("2023-08-01")
"""
