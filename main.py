import argparse
from itertools import chain
from typing import Optional

import pendulum

from conf.consts import CryptoAsset
from exec import ExecutionContext
from inject import injector
from repository.remote import BinanceClient
from vm import KlineProducer
from repository.db import DataBaseManager
from repository import TradingPair, Interval


def train():

    context = ExecutionContext(
        pair=injector.trading_pair,
        db_manager=injector.db_manager,
        execution=injector.execution,
        exec_id=injector.exec_id,
        vm=injector.vm,
        env=injector.env,
        output_dir=injector.output_dir,
        time_steps=injector.time_steps,
    )
    context.train()


def collect_data(
    start_time: pendulum.DateTime, end_time: Optional[pendulum.DateTime] = None, n_obs: Optional[float] = None
):
    """
    Get observation data from Binance API and store it in a local database
    :param start_time: open time for the first kline, it will be converted to the start of the interval
    :param end_time: close time for the last kline, it will be converted to the end of the interval
    :param n_obs: total number of records to get.
    """
    base_asset, quote_asset = CryptoAsset.BNB, CryptoAsset.BUSD

    def get_kline_history(start: pendulum.DateTime, end: pendulum.DateTime, interval: Interval = Interval.M_1) -> None:
        """
        Get kline records from the past and insert them into the database.
        :param start: open time for the first kline
        :param end: close time for the last kline
        :param interval: klines interval
        """
        if interval != Interval.M_1:
            raise ValueError("only 1 minute interval is currently supported.")

        limit = 1_000
        api_client = BinanceClient()
        db_manager = DataBaseManager.init()

        start = start.start_of("minute")
        end = end.end_of("minute")
        points = chain(pendulum.period(start, end).range("minutes", amount=limit - 1), (end,))
        start_point = next(points)

        for next_point in points:
            end_point = next_point.end_of("minute")
            for kl in api_client.get_klines_data(
                TradingPair(base_asset, quote_asset), Interval.M_1, start_point, end_point, limit
            ):
                db_manager.insert(kl)

            start_point = next_point.add(minutes=1)

    # Check arguments
    if end_time is None and n_obs is None:
        print("Collecting klines indefinitely")
        producer = KlineProducer(TradingPair(base_asset, quote_asset))
        if not producer.is_alive():
            producer.start()  # This will start getting klines from this moment onwards

        get_kline_history(start_time, pendulum.now().subtract(minutes=1))  # Get klines from the past

    elif end_time is not None:
        if n_obs is not None:
            raise ValueError("n_obs must be None when end_time is not")

        if end_time < pendulum.now():
            get_kline_history(start_time, end_time)
        else:
            # I don't think we are going to need this ever.
            raise NotImplementedError("This scenario is not supported")

    else:
        get_kline_history(start_time, start_time.add(minutes=n_obs))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--collect", default=0, type=str, help="Collect observations from the source without training an agent."
    )
    parser.add_argument(
        "-t",
        "--train",
        default=False,
        action="store_const",
        const=True,
        help="Train an agent while collecting new observations.",
    )

    args = parser.parse_args()

    if args.train:
        train()
    elif args.collect == "inf":
        collect_data(pendulum.now())
    elif isinstance(args.collect, str):
        num, unit = args.collect.split()
        if unit == "years":
            collect_data(start_time=pendulum.now().subtract(years=int(num)), end_time=pendulum.now())
        else:
            raise ValueError(f"Illegal unit: {unit}")
    elif args.collect > 0:
        collect_data(pendulum.now(), n_obs=args.collect)
