from collections import namedtuple
from typing import List

import numpy as np

Statistics = namedtuple("Statistics", ["mean", "var"])


def _running_norm_statistics(elements: List[np.ndarray]) -> List[Statistics]:
    # Normalize expected rewards
    mean = 0
    var = 1
    count = 1e-4
    norm_statistics = []
    for e in elements:
        batch_size = len(e)
        batch_mean = e.mean()
        batch_var = e.var()

        delta = batch_mean - mean
        tot_count = count + batch_size

        new_mean = mean + delta * batch_size / tot_count
        m_a = var * count
        m_b = batch_var * batch_size
        m_2 = m_a + m_b + np.square(delta) * count * batch_size / (count + batch_size)
        new_var = m_2 / (count + batch_size)

        new_count = batch_size + count

        mean = new_mean
        var = new_var
        count = new_count
        norm_statistics.append(Statistics(mean, var))

    return norm_statistics


def normalize_rewards(rewards: List[np.ndarray]) -> List[np.ndarray]:
    statistics = _running_norm_statistics(rewards)
    return [np.clip(r / np.sqrt(s.var + 1e-8), -10, 10) for r, s in zip(rewards, statistics)]


def normalize_obs(obs: List[np.ndarray]) -> List[np.ndarray]:
    statistics = _running_norm_statistics(obs)
    return [np.clip((o - s.mean) / np.sqrt(s.var + 1e-8), -10, 10) for o, s in zip(obs, statistics)]
