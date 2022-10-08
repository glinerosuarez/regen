import pendulum

from exec import DependencyInjector
from repository import Interval
from repository.db import Kline


if __name__ == "__main__":

    injector = DependencyInjector()
    db_manager = injector.db_manager
    api_clinet = injector.api_client
    pair = injector.trading_pair

    last_close_ts = db_manager.select_max(Kline.close_time)
    last_close_time = pendulum.from_timestamp(last_close_ts / 1_000)

    now = pendulum.now("UTC")

    start = last_close_time.start_of("minute").add(minutes=1)
    end = now.end_of("minute")

    counter = 0
    batch_size = 1
    for minute in pendulum.period(start, end).range("minutes", batch_size):
        open_time = minute
        close_time = minute.add(minutes=batch_size).end_of("minute")
        klines = api_clinet.get_klines_data(pair, Interval.M_1, open_time, close_time, batch_size)
        db_manager.insert(klines)
        counter += len(klines)
        print(f"{counter} klines have been inserted into the database.")
