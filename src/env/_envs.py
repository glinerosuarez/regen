import subprocess
from pathlib import Path
from typing import Optional, Tuple, Union

import gym
import numpy as np
from gym import spaces
from attr import define, field
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import VecNormalize

from conf.consts import Action, Position
from vm.crypto_vm import CryptoViewModel


def build_crypto_trading_env(vm: CryptoViewModel):
    env = make_vec_env(lambda: CryptoTradingEnv(vm), n_envs=1)
    return VecNormalize(env, norm_obs_keys=["klines"])


def load_crypto_trading_env(stats_path: Union[str, Path], vm: CryptoViewModel):
    env = make_vec_env(lambda: CryptoTradingEnv(vm), n_envs=1)
    return VecNormalize.load(stats_path, env)


@define
class CryptoTradingEnv(gym.Env):
    """Crypto asset trading environment that follows gym interface."""

    metadata = {"render.modes": ["live"]}

    vm: CryptoViewModel = field()
    shape: Tuple[int] = field(init=False)
    action_space: spaces.Discrete = field(init=False)
    observation_space: spaces.Box = field(init=False)
    first_rendering: bool = field(init=False, default=True)
    render_process: Optional[subprocess.Popen] = field(init=False, default=None)

    @shape.default
    def init_shape(self) -> Tuple[int]:
        # Shape of a single observation.
        # TODO: create a variable 'n_features' and replace the hardcoded value with it
        # 11 here means number of features, atm:
        # open, high, low, ma_7, ma_25, ma_100, ma_300, ma_1440, ma_14400, ma_144000, values
        return (self.vm.window_size * 11,)

    @action_space.default
    def init_action_space(self) -> spaces.Discrete:
        # Actions of the format Buy x%, Sell x%, Hold, etc.
        return spaces.Discrete(len(Action))

    @observation_space.default
    def init_observation_space(self) -> spaces.Dict:
        return spaces.Dict(
            {
                # Prices contain the OHCL values for the last window_size prices.
                "klines": spaces.Box(low=-np.inf, high=np.inf, shape=self.shape, dtype=np.float32),
                # Current position the agent has.
                "position": spaces.Discrete(len(Position)),
            }
        )

    def render(self, mode="human"):
        if mode == "live":
            if self.first_rendering:
                self.render_process = subprocess.Popen(["python", "env/_render.py"], start_new_session=True)
                self.first_rendering = False

    def reset(self, *, seed: Optional[int] = None, return_info: bool = False, options: Optional[dict] = None):
        # Reset rendering process.
        self.first_rendering = True
        if self.render_process:
            self.render_process.kill()
            self.render_process = None

        return self.vm.reset()

    def step(self, action):
        return self.vm.step(Action(action))
