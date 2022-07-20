import argparse
from datetime import datetime

from stable_baselines3 import PPO
from stable_baselines3.ppo.policies import MlpPolicy
from stable_baselines3.common.logger import configure
from stable_baselines3.common.cmd_util import make_vec_env

from consts import CryptoAsset
from env import CryptoTradingEnv


time_steps = 8
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


def collect_data(n_steps: int):
    """Get observation data from Binance API and store it in a local database."""
    env = CryptoTradingEnv(
        window_size=window_size, base_asset=base_asset, quote_asset=quote_asset, base_balance=100, use_db_buffer=False
    )
    env.reset()

    for step in range(n_steps):
        print("Step {}".format(step + 1))
        obs, reward, done, info = env.step(1)
        print("obs=", obs, "reward=", reward, "done=", done)
        env.render()
        if done:
            print("Goal reached!", "reward=", reward)
            env.reset()


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
