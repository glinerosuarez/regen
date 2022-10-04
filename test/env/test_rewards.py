from typing import List

import numpy as np
import pytest

from conf.consts import Action
from env import build_crypto_trading_env


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


@pytest.fixture
def prices() -> List[float]:
    return [
        23.5678,
        23.5661,
        23.5591,
        23.5635,
        23.5308,
        23.5326,
        23.5473,
        23.515,
        23.518,
        23.5213,
        23.5213,
        23.5297,
        23.5594,
        23.5594,
    ]


@pytest.fixture
def expected_rewards(prices) -> List[float]:
    return [
        0,
        0,
        0,
        0,
        ((prices[0] - prices[4]) / prices[0]) * 100,
        0,
        0,
        ((prices[6] - prices[7]) / prices[6]) * 100,
        0,
        0,
        0,
        0,
        0,
        ((prices[11] - prices[13]) / prices[11]) * 100,
    ]


@pytest.fixture
def tot_expected_reward(expected_rewards) -> float:
    # Normalize expected rewards
    mean = 0
    var = 1
    count = 1e-4
    norm_expected_rewards = []
    for r in expected_rewards:
        delta = r - mean
        tot_count = count + 1

        new_mean = mean + delta * 1 / tot_count
        m_a = var * count
        m_b = 0
        m_2 = m_a + m_b + np.square(delta) * count * 1 / (count + 1)
        new_var = m_2 / (count + 1)

        new_count = 1 + count

        mean = new_mean
        var = new_var
        count = new_count

        norm_expected_rewards.append(np.clip(r / np.sqrt(var + 1e-8), -10, 10))

    return sum(norm_expected_rewards)


def test_rewards(insert_klines, vm, actions, tot_expected_reward):
    rewards = []

    env = build_crypto_trading_env(vm)
    obs = env.reset()

    for i, a in enumerate(actions):
        action = [a]
        obs, reward, done, info = env.step(action)
        rewards.append(reward[0])

    assert round(sum(rewards), 1) == round(tot_expected_reward, 1)
