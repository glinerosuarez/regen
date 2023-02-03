{{
    config(
        materialized = 'incremental',
        on_schema_change = 'fail'
    )
}}
WITH raw_klines AS (SELECT * FROM {{ source('regen', 'klines') }})
SELECT
    id AS kline_id,
    pair,
    open_time AS open_ts,
    open_value,
    high,
    low,
    close_value,
    volume,
    close_time AS close_ts,
    quote_asset_vol,
    trades,
    taker_buy_base_vol,
    taker_buy_quote_vol,
    created_at AS created_at_date
FROM raw_klines
{% if is_incremental() %}
    WHERE open_time > (SELECT MAX(open_ts) FROM {{ this }})
{% endif %}