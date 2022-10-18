from collections import deque
from itertools import chain, tee, starmap
import os

import pendulum

from inject import injector
from repository import Interval
from repository.db import Kline, get_db_generator, MovingAvgs


def pairwise(iterable):
    # pairwise('ABCDEFG') --> AB BC CD DE EF FG
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


if __name__ == "__main__":

    if os.environ["REGEN_ENV"] != "production":
        raise ValueError("REGEN_ENV must be production.")

    db_manager = injector.db_manager
    api_clinet = injector.env_injector.api_client
    pair = injector.trading_pair

    # Compute averages for the first kline
    first_close_time = pendulum.from_timestamp(db_manager.select_min(Kline.close_time) / 1_000)

    start = first_close_time.subtract(days=100).start_of("minute")
    end = first_close_time.subtract(minutes=1)
    mins_in_between = (end - start).in_minutes()
    api_batch_size = 900

    def get_klines(s: pendulum.DateTime, e: pendulum.DateTime):
        return api_clinet.get_klines_data(pair=pair, interval=Interval.M_1, start_time=s, end_time=e, limit=1_000)

    api_close_val = map(
        lambda x: x.close_value,
        chain.from_iterable(
            starmap(get_klines, pairwise(chain(pendulum.period(start, end).range("minutes", api_batch_size), [end])))
        ),
    )
    db_klines = get_db_generator(db_manager, Kline, page_size=10_000)

    api_cv_l = list(api_close_val)
    mv_window_sizes = [144000, 14400, 1440, 300, 100, 25, 7]
    queues = [deque(api_cv_l[-ws + 1:]) for ws in mv_window_sizes]
    del api_cv_l
    init_sums = [sum(q) for q in queues]
    for kl in db_klines:
        record = {}
        for i, q in enumerate(queues):
            init_sums[i] = init_sums[i] + kl.close_value
            s = mv_window_sizes[i]
            record[f"s{s}"] = round(init_sums[i]/s, 6)

            init_sums[i] = init_sums[i] - q.popleft()
            q.append(kl.close_value)

        moving_avgs = MovingAvgs(kline_id=kl.id, **record)
        db_manager.insert(moving_avgs)
        print(f"Record {moving_avgs} successfully inserted.")
