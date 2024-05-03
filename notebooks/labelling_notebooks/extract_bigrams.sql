SELECT
    BERT_topic,
    GSDMM_topic,
    ARRAY_AGG(DISTINCT term) AS unique_terms
FROM
    `@project.@topics_table`, UNNEST(terms) AS t
WHERE
    uuid = "@UUID"
GROUP BY
    BERT_topic, GSDMM_topic
ORDER BY
    BERT_topic,
    GSDMM_topic
