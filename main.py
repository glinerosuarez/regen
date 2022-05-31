from datetime import datetime

from stable_baselines3 import PPO, A2C
from stable_baselines3.ppo.policies import MlpPolicy
from stable_baselines3.common.logger import configure
from stable_baselines3.common.cmd_util import make_vec_env

from consts import CryptoAsset
from env import CryptoTradingEnv


def train():
    timesteps = 5

    env = CryptoTradingEnv(window_size=5, base_asset=CryptoAsset.BNB, quote_asset=CryptoAsset.BUSD, base_balance=100)
    env = make_vec_env(lambda: env, n_envs=1)

    # set up logger
    tmp_path = "output/logs/"
    new_logger = configure(tmp_path, ["stdout", "csv", "tensorboard"])

    model = A2C(MlpPolicy, env, verbose=1)
    model.set_logger(new_logger)
    model.learn(total_timesteps=timesteps)

    ts = datetime.today()
    model.save(
        f"output/models/PPO_{env.base_asset.name}{env.quote_asset.name}_{timesteps}_{ts.year}{ts.month}{ts.day}"
        f"{ts.hour}{ts.minute}{ts.second}"
    )


if __name__ == '__main__':
    train()
