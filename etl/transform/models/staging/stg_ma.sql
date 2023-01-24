WITH src_klines AS (
    SELECT * FROM {{ ref('src_klines') }}
)
SELECT
    kline_id
    , close_value
    , SUM(close_value) OVER (ORDER BY open_ts ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING) AS sum_last_7
    , LAG(close_value, 7) OVER (ORDER BY open_ts) AS first_last_7
    , SUM(close_value) OVER (ORDER BY open_ts ROWS BETWEEN 25 PRECEDING AND 1 PRECEDING) AS sum_25
    , LAG(close_value, 25) OVER (ORDER BY open_ts) AS first_last_25
    , SUM(close_value) OVER (ORDER BY open_ts ROWS BETWEEN 100 PRECEDING AND 1 PRECEDING) AS sum_100
    , LAG(close_value, 100) OVER (ORDER BY open_ts) AS first_last_100
    , SUM(close_value) OVER (ORDER BY open_ts ROWS BETWEEN 300 PRECEDING AND 1 PRECEDING) AS sum_300
    , LAG(close_value, 300) OVER (ORDER BY open_ts) AS first_last_300
    , SUM(close_value) OVER (ORDER BY open_ts ROWS BETWEEN 1440 PRECEDING AND 1 PRECEDING) AS sum_1440
    , LAG(close_value, 1440) OVER (ORDER BY open_ts) AS first_last_1440
    , SUM(close_value) OVER (ORDER BY open_ts ROWS BETWEEN 14400 PRECEDING AND 1 PRECEDING) AS sum_14400
    , LAG(close_value, 14400) OVER (ORDER BY open_ts) AS first_last_14400
    , SUM(close_value) OVER (ORDER BY open_ts ROWS BETWEEN 144000 PRECEDING AND 1 PRECEDING) AS sum_144000
    , LAG(close_value, 144000) OVER (ORDER BY open_ts) AS first_last_144000
FROM
    src_klines
ORDER BY
    open_ts
