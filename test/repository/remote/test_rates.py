import pendulum

import configuration
from consts import CryptoAsset
from repository import TradingPair, Interval
from repository.db import DataBaseManager
from repository.remote import BinanceClient

if __name__ == '__main__':

    def get_kline_history(start: pendulum.DateTime, end: pendulum.DateTime, interval: Interval = Interval.M_1):
        if interval != Interval.M_1:
            raise ValueError("only 1 minute interval is currently supported.")

        limit = 1_000

        api_client = BinanceClient()
        db_manager = DataBaseManager(configuration.settings.db_name)

        start = start.start_of("minute")
        end = end.end_of("minute")
        points = iter([m for m in pendulum.period(start, end).range("minutes", amount=limit - 1)])
        start_point = next(points)

        for next_point in points:
            end_point = next_point.end_of("minute")
            for kl in api_client.get_klines_data(
                TradingPair(CryptoAsset.BNB, CryptoAsset.BUSD),
                Interval.M_1,
                start_point,
                end_point,
                limit
            ):
                db_manager.insert(kl)

            start_point = next_point.add(minutes=1)

    now = pendulum.now()
    get_kline_history(now.subtract(years=2), now)
