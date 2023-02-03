import pendulum
from airflow.decorators import task

import conf
from log import LoggerFactory
from repository.db import DataBaseManager
from repository.remote import BinanceClient
from repository import Interval, TradingPair


@task
def extract_kline_minutes(dag_run=None) -> int:
    """
    #### Extract specific kline task
    Get specific kline data from Binance api.
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
    api_client = BinanceClient(
        base_urls=settings.bnb_base_urls,
        client_key=settings.bnb_client_key,
        client_secret=settings.bnb_client_secret,
        db_manager=db_manager,
        logger=LoggerFactory.get_console_logger("BinanceClient"),
    )
    pair = TradingPair(settings.base_asset, settings.quote_asset)
    start = pendulum.instance(dag_run.data_interval_start, tz="UTC")
    end = pendulum.instance(dag_run.data_interval_end, tz="UTC").subtract(minutes=1).end_of("minute")
    print(f"Getting klines from {start} to {end}.")

    batch_size = 1
    kline = api_client.get_klines_data(pair, Interval.M_1, start, end, batch_size)[0]
    db_manager.insert(kline)
    print(f"{kline} has been inserted into the database.")
    return kline.id
