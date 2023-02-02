WITH last_klines AS (
    SELECT close_value
    FROM {{ ref('src_klines') }}
    WHERE open_ts >= EXTRACT(EPOCH FROM NOW() - INTERVAL '100 days') * 1000
    ORDER BY open_ts DESC
)
, ma7 AS (SELECT 1 AS id, AVG(close_value) AS ma FROM (SELECT close_value FROM last_klines LIMIT 7) l7)
, ma25 AS (SELECT 1 AS id, AVG(close_value) AS ma FROM (SELECT close_value FROM last_klines LIMIT 25) l25)
, ma100 AS (SELECT 1 AS id, AVG(close_value) AS ma FROM (SELECT close_value FROM last_klines LIMIT 100) l100)
, ma300 AS (SELECT 1 AS id, AVG(close_value) AS ma FROM (SELECT close_value FROM last_klines LIMIT 300) l300)
, ma1day AS (SELECT 1 AS id, AVG(close_value) AS ma FROM (SELECT close_value FROM last_klines LIMIT 1440) l1440)
, ma10day AS (SELECT 1 AS id, AVG(close_value) AS ma FROM (SELECT close_value FROM last_klines LIMIT 14400) l14400)
, ma100day AS (SELECT 1 AS id, AVG(close_value) AS ma FROM (SELECT close_value FROM last_klines LIMIT 144000) l144000)

SELECT
    ma7.ma AS ma7
    , ma25.ma AS ma25
    , ma100.ma AS ma100
    , ma300.ma AS ma300
    , ma1day.ma AS ma1day
    , ma10day.ma AS ma10day
    , ma100day.ma AS ma100day
FROM
    ma7
    JOIN ma25 ON ma7.id = ma25.id
    JOIN ma100 ON ma7.id = ma100.id
    JOIN ma300 ON ma7.id = ma300.id
    JOIN ma1day ON ma7.id = ma1day.id
    JOIN ma10day ON ma7.id = ma10day.id
    JOIN ma100day ON ma7.id = ma100day.id


