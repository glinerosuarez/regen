import logging
from pathlib import Path

import pendulum
from airflow.decorators import task

import conf
from log import LoggerFactory
from repository.db import Kline
from repository.db import DataBaseManager
from repository.remote import BinanceClient
from repository import Interval, TradingPair


@task
def extract_klines():
    """
    #### Extract klines task
    Get klines data from Binance api.
    """
    print(f"Taks: extract_klines, are there config files: {Path('./regen_config_files/etl_settings.toml').is_file()}")

    def get_logger(name: str, security_level: int = logging.INFO) -> logging.Logger:
        return LoggerFactory.get_file_logger(name, security_level=security_level)

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
        logger=get_logger("BinanceClient"),
    )
    pair = TradingPair(settings.base_asset, settings.quote_asset)

    last_close_ts = db_manager.select_max(Kline.close_time)
    last_close_time = pendulum.from_timestamp(last_close_ts / 1_000)
    now = pendulum.now("UTC")
    start = last_close_time.start_of("minute").add(minutes=1)
    end = now.end_of("minute")

    counter = 0
    batch_size = 900
    for minute in pendulum.period(start, end).range("minutes", batch_size):
        open_time = minute
        close_time = minute.add(minutes=batch_size).end_of("minute")
        klines = api_client.get_klines_data(pair, Interval.M_1, open_time, close_time, batch_size)
        db_manager.insert(klines)
        counter += len(klines)
        print(f"{counter} klines have been inserted into the database.")
