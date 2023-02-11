WITH src_klines AS (
    SELECT * FROM {{ ref('src_klines') }}
), ma AS (
    SELECT * FROM {{ ref('src_mas') }}
)
SELECT
    sk.kline_id AS kline_id
    --, sk.pair AS pair
    , sk.open_value AS open_value
    , sk.high AS high
    , sk.low AS low
    , sk.close_value AS close_value
    --, sk.close_ts AS close_ts
    , ma.ma_7 AS ma_7
    , ma.ma_25 AS ma_25
    , ma.ma_100 AS ma_100
    , ma.ma_300 AS ma_300
    , ma.ma_1440 AS ma_1440
    , ma.ma_14400 AS ma_14400
    , ma.ma_144000 AS ma_144000
    , sk.open_ts AS open_ts
FROM
    src_klines sk INNER JOIN ma ON sk.kline_id = ma.kline_id
