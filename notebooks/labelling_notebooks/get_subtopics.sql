SELECT
    * EXCEPT(terms)
FROM
    `@project.@topics_table`
WHERE
    uuid = "@UUID"
