import argparse
from datetime import datetime
from itertools import chain
from typing import Optional

import pendulum
from stable_baselines3 import PPO
from stable_baselines3.common.logger import configure
from stable_baselines3.common.cmd_util import make_vec_env

import configuration
from consts import CryptoAsset
from env import CryptoTradingEnv
from repository.remote import BinanceClient
from vm import KlineProducer
from repository.db import DataBaseManager
from repository import TradingPair, Interval

time_steps = 1_000_000
window_size = 1_440
base_asset = CryptoAsset.BNB
quote_asset = CryptoAsset.BUSD


def train():
    # TODO: Save logs and progress per execution
    # TODO: Normalize observations with stable_baselines3.common.vec_env.VecNormalize
    # TODO: Train with more than 1 vectorized DummyVecEnv
    # TODO: Customize actor/critic architecture, can I use Transformers? LSTM feature extractors?
    # TODO: Use callbacks to get bets models or to log values
    # TODO: Implement tensorboard, weights and biases
    # TODO: Useful scripts here: https://github.com/DLR-RM/rl-baselines3-zoo

    env = CryptoTradingEnv(window_size=window_size, base_asset=base_asset, quote_asset=quote_asset, base_balance=100)
    env = make_vec_env(lambda: env, n_envs=1)

    # set up logger
    tmp_path = "output/logs/"
    new_logger = configure(tmp_path, ["stdout", "csv", "tensorboard"])

    model = PPO("MultiInputPolicy", env, verbose=1)
    model.set_logger(new_logger)
    model.learn(total_timesteps=time_steps)

    ts = datetime.today()
    model.save(
        f"output/models/PPO_{base_asset.name}{quote_asset.name}_{time_steps}_{ts.year}{ts.month}{ts.day}"
        f"{ts.hour}{ts.minute}{ts.second}"
    )


def collect_data(
    start_time: pendulum.DateTime, end_time: Optional[pendulum.DateTime] = None, n_obs: Optional[float] = None
):
    """
    Get observation data from Binance API and store it in a local database
    :param start_time: open time for the first kline, it will be converted to the start of the interval
    :param end_time: close time for the last kline, it will be converted to the end of the interval
    :param n_obs: total number of records to get.
    """

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
        db_manager = DataBaseManager(configuration.settings.db_name)

        start = start.start_of("minute")
        end = end.end_of("minute")
        points = chain(pendulum.period(start, end).range("minutes", amount=limit - 1), (end,))
        start_point = next(points)

        for next_point in points:
            end_point = next_point.end_of("minute")
            for kl in api_client.get_klines_data(
                TradingPair(CryptoAsset.BNB, CryptoAsset.BUSD), Interval.M_1, start_point, end_point, limit
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
