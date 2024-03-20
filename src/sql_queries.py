query_labelled_feedback = """

SELECT
    feedback.type as feedback_type,
    DATE(feedback.created) AS created,
    feedback.subject_page_path as url,
    CONCAT('https://www.gov.uk', feedback.subject_page_path) AS full_url,
    CAST(feedback.feedback_record_id AS STRING) AS feedback_record_id,
    feedback.response_value as feedback,
    labels.labels,
    IFNULL(CAST(labels.urgency AS INT), -1) as urgency,
    feedback.organisation as department,
    feedback.primary_organisation as primary_department,
    feedback.document_type,
    feedback.embeddings,
    feedback.sentiment,
    feedback.spam_classification,
    feedback.spam_probability,
    feedback.publishing_app,
    feedback.locale,
    feedback.title as page_title,
    feedback.taxons
FROM @PUBLISHING_VIEW feedback
JOIN @LABELLED_FEEDBACK_TABLE labels
  ON CAST(feedback.feedback_record_id AS INT)=CAST(labels.id AS INT)
WHERE feedback.created > DATE("2023-08-01")
AND document_type != "special route"
"""


query_distinct_page_paths = """
SELECT DISTINCT subject_page_path FROM @PUBLISHING_VIEW
"""

query_distinct_orgs = """
SELECT DISTINCT organisation FROM @PUBLISHING_VIEW, UNNEST(organisation) as organisation
"""

query_distinct_doc_type = """
SELECT DISTINCT document_type FROM @PUBLISHING_VIEW
"""
