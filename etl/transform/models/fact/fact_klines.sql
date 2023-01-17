WITH src_klines AS (
    SELECT * FROM {{ ref('src_klines') }}
)
SELECT
    kline_id,
    pair,
    open_ts,
    open_value,
    high,
    low,
    close_value,
    volume,
    close_ts,
    AVG(close_value) OVER (ORDER BY open_ts ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as ma_7,
    AVG(close_value) OVER (ORDER BY open_ts ROWS BETWEEN 24 PRECEDING AND CURRENT ROW) as ma_25,
    AVG(close_value) OVER (ORDER BY open_ts ROWS BETWEEN 99 PRECEDING AND CURRENT ROW) as ma_100,
    AVG(close_value) OVER (ORDER BY open_ts ROWS BETWEEN 299 PRECEDING AND CURRENT ROW) as ma_300,
    AVG(close_value) OVER (ORDER BY open_ts ROWS BETWEEN 1439 PRECEDING AND CURRENT ROW) as ma_1440,
    AVG(close_value) OVER (ORDER BY open_ts ROWS BETWEEN 14399 PRECEDING AND CURRENT ROW) as ma_14400,
    AVG(close_value) OVER (ORDER BY open_ts ROWS BETWEEN 143999 PRECEDING AND CURRENT ROW) as ma_144000
FROM src_klines