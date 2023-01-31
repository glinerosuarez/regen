from airflow.decorators import task

import conf
from repository.db import DataBaseManager


@task
def insert_ma(kline_id: int) -> int:
    """
    #### Task, for inserting a new moving average record to the database.
    Insert a new moving average record to the database.
    """
    settings = conf.load_settings(
        settings_path="./regen_config_files/etl_settings.toml", secrets_path="./regen_config_files/.etl_secrets.toml"
    )
    db_manager = DataBaseManager(
        db_name=settings.db_name,
        engine_type=DataBaseManager.EngineType.PostgreSQL,
        host=settings.db_host,
        user=settings.db_user,
        password=settings.db_password,
    )

    print(f"Inserting new ma record for kline id: {kline_id}.")

    # Get moving averages
    ma7min = db_manager.select_avg(table="stg_last7min_klines", schema="dev", column="close_value")
    ma25min = db_manager.select_avg(table="stg_last25min_klines", schema="dev", column="close_value")
    ma100min = db_manager.select_avg(table="stg_last100min_klines", schema="dev", column="close_value")
    ma300min = db_manager.select_avg(table="stg_last300min_klines", schema="dev", column="close_value")
    ma1day = db_manager.select_avg(table="stg_lastday_klines", schema="dev", column="close_value")
    ma10days = db_manager.select_avg(table="stg_last10days_klines", schema="dev", column="close_value")
    ma100days = db_manager.select_avg(table="stg_last100days_klines", schema="dev", column="close_value")

    print(
        f"Inserting "
        f"ma7min: {ma7min}, "
        f"ma25min: {ma25min}, "
        f"ma100min: {ma100min}, "
        f"ma300min: {ma300min}, "
        f"ma1day: {ma1day}"
        f"ma10days: {ma10days}"
        f"ma100days: {ma100days}"
    )

    db_manager.insert(
        records=[kline_id, ma7min, ma25min, ma100min, ma300min, ma1day, ma10days, ma100days],
        table="stg_ma",
        columns=["kline_id", "ma_7", "ma_25", "ma_100", "ma_300", "ma_1440", "ma_14400", "ma_144000"]
    )
    print(f"MA's have been inserted into the database.")
