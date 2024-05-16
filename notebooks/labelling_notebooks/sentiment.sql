WITH
  topics AS (
  SELECT
    uuid,
    created,
    record_id,
    topics
  FROM
    @project.@topics_table
  WHERE
    uuid = '@uuid'),
  process AS (
  SELECT
    feedback_record_id,
    sentiment
  FROM
    @project.@process_table
  WHERE
    DATE(created) >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR))
SELECT
  *
FROM
  topics
LEFT JOIN
  process
ON
  topics.record_id = process.feedback_record_id
