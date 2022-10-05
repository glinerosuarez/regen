import gym
import pytest

from env import build_crypto_trading_env


@pytest.fixture
def env(vm) -> gym.Env:
    return build_crypto_trading_env(vm)
