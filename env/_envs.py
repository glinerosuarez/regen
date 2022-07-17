import subprocess
from typing import Optional

import gym
import numpy as np
from gym import spaces
from vm.consts import Action
from attr import define, field
from consts import CryptoAsset
from vm.crypto_vm import CryptoViewModel


@define
class CryptoTradingEnv(gym.Env):
    """Crypto asset trading environment that follows gym interface."""

    metadata = {"render.modes": ["live"]}

    window_size: int = field()
    base_asset: CryptoAsset = field()
    quote_asset: CryptoAsset = field()
    base_balance: float = field()
    shape: tuple[int, int] = field(init=False)
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
    def init_shape(self) -> tuple[int, int]:
        # Shape of a single observation.
        return self.window_size, 5

    @action_space.default
    def init_action_space(self) -> spaces.Discrete:
        # Actions of the format Buy x%, Sell x%, Hold, etc.
        return spaces.Discrete(len(Action))

    @observation_space.default
    def init_observation_space(self) -> spaces.Box:
        # Prices contain the OHCL values for the last window_size prices.
        return spaces.Box(low=0.0, high=np.inf, shape=self.shape, dtype=np.float32)

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
