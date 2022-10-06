from typing import List

import gym
import pytest

from conf.consts import Action
from env import build_crypto_trading_env


@pytest.fixture
def env(vm) -> gym.Env:
    return build_crypto_trading_env(vm)


@pytest.fixture
def actions() -> List[Action]:
    return [
        Action.Sell,
        Action.Sell,
        Action.Sell,
        Action.Sell,
        Action.Buy,
        Action.Buy,
        Action.Sell,
        Action.Buy,
        Action.Buy,
        Action.Buy,
        Action.Buy,
        Action.Sell,
        Action.Sell,
        Action.Buy,
    ]
