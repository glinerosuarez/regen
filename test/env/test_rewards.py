from typing import List

import numpy as np
import pytest

from test.env.utils import normalize_rewards


@pytest.fixture
def prices() -> List[np.ndarray]:
    return [
        np.array(p, np.float32)
        for p in [
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
    ]


@pytest.fixture
def expected_rewards(prices) -> List[np.ndarray]:
    return [
        np.expand_dims(np.array(r, np.float32), axis=0)
        for r in [
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
    ]


@pytest.fixture
def norm_expected_rewards(expected_rewards) -> List[float]:
    norm_rewards = normalize_rewards(expected_rewards)
    norm_rewards = np.squeeze(np.array(norm_rewards)).tolist()
    return norm_rewards


# TODO: fix this test
"""def test_rewards(insert_klines, env, actions, norm_expected_rewards):
    rewards = []

    env.reset()

    for i, a in enumerate(actions):
        action = [a]
        obs, reward, done, info = env.step(action)
        rewards.append(reward[0])
    assert np.array_equal(
        np.round(rewards, 6).astype(np.float32), np.round(norm_expected_rewards, 6).astype(np.float32)
    )"""
