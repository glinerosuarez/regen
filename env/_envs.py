from typing import Optional, Union

import gym
import numpy as np
from gym import spaces
from gym.core import ObsType
from consts import CryptoAsset
from vm.consts import Action
from vm.crypto_vm import CryptoViewModel


class CryptoTradingEnv(gym.Env):
    """Crypto asset trading environment that follows gym interface."""

    def render(self, mode="human"):
        pass

    def __init__(
            self,
            window_size: int,
            base_asset: CryptoAsset,
            quote_asset: CryptoAsset,
            base_balance: float,
            quote_balance: float,
    ):
        # VM to get data from sources.
        self.vm = CryptoViewModel(
            base_asset=base_asset,
            quote_asset=quote_asset,
            window_size=window_size,
            base_balance=base_balance,
            quote_balance=quote_balance,
        )

        # Shape of a single observation.
        self.shape = window_size
        # Spaces
        # Actions of the format Buy x%, Sell x%, Hold, etc.
        self.action_space = spaces.Discrete(len(Action))
        # Prices contain the OHCL values for the last window_size prices.
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=self.shape, dtype=np.float32)

    def reset(
            self, *, seed: Optional[int] = None, return_info: bool = False, options: Optional[dict] = None
    ) -> Union[ObsType, tuple[ObsType, dict]]:
        return self.vm.reset()

    def step(self, action):
        return self.vm.step(action)
