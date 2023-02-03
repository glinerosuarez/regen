from airflow.decorators import task

import conf
from repository.db import DataBaseManager


@task
def insert_ma(kline_id: int) -> None:
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
    last_ma = db_manager.select_first_row(table="stg_last_ma", schema="dev")

    print(f"Inserting last MA's {last_ma}")

    db_manager.insert(
        records=[str(v) for v in [kline_id, *last_ma]],
        table="dev.stg_ma",
        columns=["kline_id", "ma_7", "ma_25", "ma_100", "ma_300", "ma_1440", "ma_14400", "ma_144000"],
    )
    print(f"MA's have been inserted into the database.")
