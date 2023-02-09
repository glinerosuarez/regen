from collections import deque
from itertools import chain, tee, starmap

import pendulum
from airflow.decorators import task

import conf
from log import LoggerFactory
from repository import Interval, TradingPair
from repository.db import Kline, get_db_generator, DataBaseManager, MovingAvgs
from repository.remote import BinanceClient


def pairwise(iterable):
    # pairwise('ABCDEFG') --> AB BC CD DE EF FG
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


@task
def populate_mas():
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

    # Compute averages for the first kline
    first_close_time = pendulum.from_timestamp(db_manager.select_min(Kline.close_time) / 1_000)

    start = first_close_time.subtract(days=100).start_of("minute")
    end = first_close_time.subtract(minutes=1)
    api_batch_size = 900

    def get_klines(s: pendulum.DateTime, e: pendulum.DateTime):
        klines = api_client.get_klines_data(
            pair=TradingPair(base=settings.base_asset, quote=settings.quote_asset),
            interval=Interval.M_1,
            start_time=s,
            end_time=e,
            limit=1_000
        )
        return klines

    cv_before_first_kline = list(
        map(
            lambda x: x.close_value,
            chain.from_iterable(
                starmap(
                    get_klines,
                    pairwise(
                        chain(
                            pendulum.period(start, end).range("minutes", api_batch_size),
                            [end],
                        )
                    ),
                )
            ),
        )
    )
    db_klines = get_db_generator(db_manager, Kline, page_size=10_000)

    window_sizes = [144_000, 14_400, 1_440, 300, 100, 25, 7]
    print(f"len(cv_before_first_kline): {len(cv_before_first_kline)}")
    queues = [deque(cv_before_first_kline[-ws + 1:]) for ws in window_sizes]
    init_sums = [sum(q) for q in queues]

    for kl in db_klines:
        record = {}
        for i, q in enumerate(queues):
            init_sums[i] = init_sums[i] + kl.close_value
            s = window_sizes[i]
            record[f"ma_{s}"] = round(init_sums[i] / s, 6)

            init_sums[i] = init_sums[i] - q.popleft()
            q.append(kl.close_value)

        moving_avgs = MovingAvgs(kline_id=kl.id, **record)
        db_manager.insert(moving_avgs)
        print(f"Record {moving_avgs} successfully inserted.")
