WITH RankedTextData AS (
    SELECT
        topics,
        probs,
        text_value,
        ROW_NUMBER() OVER (PARTITION BY topics ORDER BY probs DESC) AS row_num
    FROM
        @FEEDBACK_PROJECT.@TOPICS_TABLE
    WHERE
        uuid = '@UUID'
    ),
    RankedNGramsData AS (
    SELECT
        topic AS ngram_topic,
        term,
        probability AS ngram_probability,
        ROW_NUMBER() OVER (PARTITION BY topic ORDER BY probability DESC) AS row_num
    FROM
        @FEEDBACK_PROJECT.@N_GRAM_TABLE
        WHERE
        uuid = '@UUID'
    )

    SELECT
        t.topics,
        t.probs AS text_probabilities,
        t.text_value,
        n.ngram_topic,
        n.term,
        n.ngram_probability
    FROM
        RankedTextData t
    JOIN
        RankedNGramsData n
    ON
        t.topics = n.ngram_topic
    AND
        t.row_num = n.row_num
    WHERE
        t.row_num <= 10
    ORDER BY
        t.topics,
        t.probs DESC;
