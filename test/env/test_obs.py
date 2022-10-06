from typing import List

import numpy as np
import pytest

from test.env.utils import normalize_obs


@pytest.fixture
def trade_prices(klines_data, window_size) -> List[float]:
    tp = [23.589216190521284]
    update_tp = [i + window_size for i in [0, 4, 6, 7, 11, 13]]
    for i in range(window_size, len(klines_data)):
        if i in update_tp:
            last_tp = klines_data[i - 1].close_value
            tp.append(last_tp)
        else:
            tp.append(last_tp)

    return tp


@pytest.fixture
def expected_obs(klines_data, window_size, trade_prices) -> List[np.ndarray]:
    obs = []

    klines_data = np.array(
        [np.array([kl.open_value, kl.high, kl.low, kl.close_value], dtype="float32") for kl in klines_data]
    )

    for i, tp in enumerate(trade_prices):
        klines = klines_data[i : window_size + i]
        klines = (klines - tp) / tp  # divide by last traded price
        klines = np.expand_dims(klines.flatten(), axis=0)
        obs.append(klines)

    return normalize_obs(obs)


def test_normalized_obs(insert_klines, env, expected_obs, actions):
    obs = env.reset()
    assert np.array_equal(obs["klines"], expected_obs[0])

    for i, a in enumerate(actions):
        action = [a]
        obs, reward, done, info = env.step(action)
        assert np.array_equal(obs["klines"], expected_obs[i + 1])
