{{
    config(
        materialized = 'table',
    )
}}
WITH src_klines AS (
    SELECT * FROM {{ ref('src_klines') }}
)
SELECT
    kline_id
    , AVG(close_value) OVER (ORDER BY open_ts ROWS BETWEEN 7 - 1 PRECEDING AND CURRENT ROW) AS ma_7
    , AVG(close_value) OVER (ORDER BY open_ts ROWS BETWEEN 25 - 1 PRECEDING AND CURRENT ROW) AS ma_25
    , AVG(close_value) OVER (ORDER BY open_ts ROWS BETWEEN 100 - 1 PRECEDING AND CURRENT ROW) AS ma_100
    , AVG(close_value) OVER (ORDER BY open_ts ROWS BETWEEN 300 - 1 PRECEDING AND CURRENT ROW) AS ma_300
    , AVG(close_value) OVER (ORDER BY open_ts ROWS BETWEEN 1440 - 1 PRECEDING AND CURRENT ROW) AS ma_1440
    , AVG(close_value) OVER (ORDER BY open_ts ROWS BETWEEN 14400 - 1 PRECEDING AND CURRENT ROW) AS ma_14400
    , AVG(close_value) OVER (ORDER BY open_ts ROWS BETWEEN 144000 - 1 PRECEDING AND CURRENT ROW) AS ma_144000
FROM
    src_klines
