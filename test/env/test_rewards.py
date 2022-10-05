from typing import List

import numpy as np
import pytest

from conf.consts import Action
from test.env.utils import normalize_rewards


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
    norm_rewards = normalize_rewards([np.array([r]) for r in expected_rewards])
    return sum(norm_rewards)[0]


def test_rewards(insert_klines, env, actions, tot_expected_reward):
    rewards = []

    env.reset()

    for i, a in enumerate(actions):
        action = [a]
        obs, reward, done, info = env.step(action)
        rewards.append(reward[0])

    assert round(sum(rewards), 1) == round(tot_expected_reward, 1)
