{{
    config(
        materialized = 'view',
        on_schema_change = 'fail',
    )
}}
WITH raw_moving_avgs AS (SELECT * FROM {{ source('regen', 'moving_avgs') }})
SELECT
    id AS ma_id
    , kline_id
    , ma_7
    , ma_25
    , ma_100
    , ma_300
    , ma_1440
    , ma_14400
    , ma_144000
    , created_at
FROM raw_moving_avgs
