WITH src_klines AS (
    SELECT * FROM {{ ref('src_klines') }}
)
SELECT close_value FROM src_klines WHERE open_ts >= EXTRACT(EPOCH FROM NOW() - INTERVAL '25 minutes') * 1000