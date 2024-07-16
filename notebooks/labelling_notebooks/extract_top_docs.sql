SELECT
    BERT_topic,
    GSDMM_topic,
    sentence,
    probability,
FROM (
    SELECT
        uuid,
        BERT_topic,
        GSDMM_topic,
        sentence,
        probability,
        ROW_NUMBER() OVER (PARTITION BY BERT_TOPIC, GSDMM_topic ORDER BY probability DESC) AS rn
    FROM
        `@project.@topics_table`
    WHERE
        uuid = "@UUID"
)
WHERE rn <= 10
ORDER BY BERT_topic ASC, GSDMM_topic ASC, rn ASC
