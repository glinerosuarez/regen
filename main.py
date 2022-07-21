import argparse
from datetime import datetime

from stable_baselines3 import PPO
from stable_baselines3.ppo.policies import MlpPolicy
from stable_baselines3.common.logger import configure
from stable_baselines3.common.cmd_util import make_vec_env

import configuration
from consts import CryptoAsset
from env import CryptoTradingEnv
from repository import TradingPair, Observation
from repository.db import DataBaseManager
from vm.crypto_vm import ObsProducer

time_steps = 9
window_size = 5
base_asset = CryptoAsset.BNB
quote_asset = CryptoAsset.BUSD


def train():
    env = CryptoTradingEnv(window_size=window_size, base_asset=base_asset, quote_asset=quote_asset, base_balance=100)
    env = make_vec_env(lambda: env, n_envs=1)

    # set up logger
    tmp_path = "output/logs/"
    new_logger = configure(tmp_path, ["stdout", "csv", "tensorboard"])

    model = PPO(MlpPolicy, env, verbose=1, n_steps=time_steps, batch_size=time_steps)
    model.set_logger(new_logger)
    model.learn(total_timesteps=time_steps)

    ts = datetime.today()
    model.save(
        f"output/models/PPO_{base_asset.name}{quote_asset.name}_{time_steps}_{ts.year}{ts.month}{ts.day}"
        f"{ts.hour}{ts.minute}{ts.second}"
    )


def collect_data(n_obs: int):
    """Get observation data from Binance API and store it in a local database."""
    DataBaseManager.init_connection(configuration.settings.db_name)  # Create connection to database
    DataBaseManager.create_all()

    last_exec_id = DataBaseManager.select_max(Observation.execution_id, Observation.execution_id.like('c%'))
    if last_exec_id is None:
        exec_id = "c1"
    else:
        exec_id = "c" + str(int(last_exec_id[1:]) + 1)
    episode_id = 1

    producer: ObsProducer = ObsProducer(TradingPair(base_asset, quote_asset), window_size, exec_id, False)
    step = 0
    for _ in range(1, n_obs + 1):
        step += 1
        print(f"Episode {episode_id}")
        print(f"Step {step}")
        obs, _ = producer.get_observation(episode_id)
        print("obs=", obs)
        if step + window_size >= configuration.settings.ticks_per_episode:
            print("End of episode reached!")
            step = 0
            episode_id += 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-c', '--collect', default='0', type=int, help='Collect observations from the source without training an agent.'
    )
    parser.add_argument(
        '-t', '--train',
        default=False,
        action='store_const',
        const=True,
        help='Train an agent while collecting new observations.'
    )

    args = parser.parse_args()

    if args.collect > 0:
        collect_data(args.collect)
    else:
        train()
