import subprocess
from typing import Optional, Tuple

import gym
import numpy as np
from gym import spaces
from attr import define, field
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import VecNormalize

from conf.consts import CryptoAsset, Action, Position
from vm.crypto_vm import CryptoViewModel


def build_crypto_trading_env(window_size: int, base_asset: CryptoAsset, quote_asset: CryptoAsset, base_balance: float):
    env = _CryptoTradingEnv(
        window_size=window_size, base_asset=base_asset, quote_asset=quote_asset, base_balance=base_balance
    )
    env = make_vec_env(lambda: env, n_envs=1)
    # TODO: Don't forget to save the VecNormalize statistics when saving the agent
    return VecNormalize(env, norm_obs=False, norm_reward=True)


@define
class _CryptoTradingEnv(gym.Env):
    """Crypto asset trading environment that follows gym interface."""

    metadata = {"render.modes": ["live"]}

    window_size: int = field()
    base_asset: CryptoAsset = field()
    quote_asset: CryptoAsset = field()
    base_balance: float = field()
    shape: Tuple[int] = field(init=False)
    vm: CryptoViewModel = field(init=False)
    action_space: spaces.Discrete = field(init=False)
    observation_space: spaces.Box = field(init=False)
    first_rendering: bool = field(init=False, default=True)
    render_process: Optional[subprocess.Popen] = field(init=False, default=None)

    @vm.default
    def init_vm(self):
        return CryptoViewModel(  # VM to get data from sources.
            base_asset=self.base_asset,
            quote_asset=self.quote_asset,
            window_size=self.window_size,
            base_balance=self.base_balance,
        )

    @shape.default
    def init_shape(self) -> Tuple[int]:
        # Shape of a single observation.
        return self.window_size * 4  # 5 here means number of features, atm: open, high, low, close and volume values

    @action_space.default
    def init_action_space(self) -> spaces.Discrete:
        # Actions of the format Buy x%, Sell x%, Hold, etc.
        return spaces.Discrete(len(Action))

    @observation_space.default
    def init_observation_space(self) -> spaces.Dict:
        return spaces.Dict(
            {
                # Prices contain the OHCL values for the last window_size prices.
                "klines": spaces.Box(low=-np.inf, high=np.inf, shape=(self.shape,), dtype=np.float32),
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
