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
AND feedback.document_type != "special route"
ORDER BY feedback_record_id
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

query_evaluation_data = """
SELECT
    id,
    ARRAY_TO_STRING(labels, ", ") as labels,
    urgency
FROM
    @EVALUATION_TABLE
"""

query_all_feedback = """
WITH CTE AS (
  SELECT feedback_record_id,
  STRING_AGG(response_value, ', ') AS response_value_full
FROM
  `govuk-ai-publishing.joined_feedback_view.feedback_6mth_with_metadata_updated`
GROUP BY
  feedback_record_id
)
SELECT
    feedback.type as feedback_type,
    DATE(feedback.created) AS created,
    feedback.subject_page_path as url,
    CONCAT('https://www.gov.uk', feedback.subject_page_path) AS full_url,
    CAST(feedback.feedback_record_id AS STRING) AS feedback_record_id,
    cte.response_value_full as feedback,
    CAST(ROUND(RAND() * 3) as INT64) as urgency,
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
FROM `govuk-ai-publishing.joined_feedback_view.feedback_6mth_with_metadata_updated` feedback
JOIN CTE
ON feedback.feedback_record_id=CTE.feedback_record_id
WHERE feedback.created > DATE("2023-08-01")
AND feedback.document_type != "special route"
ORDER BY feedback_record_id desc
LIMIT 100000
"""
