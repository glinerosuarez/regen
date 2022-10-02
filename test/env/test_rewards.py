import numpy as np

import conf
from conf.consts import CryptoAsset, Action
from env import build_crypto_trading_env
from repository.db import DataBaseManager


def test_rewards(insert_klines):

    actions = [
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

    prices = [
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

    expected_rewards = [
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

    tot_expected_reward = sum(norm_expected_rewards)

    rewards = []
    # DataBaseManager._engine = None
    # del db_client
    # conf.settings.db_name = "test_rewards"
    env = build_crypto_trading_env(
        window_size=5, base_asset=CryptoAsset.BNB, quote_asset=CryptoAsset.BUSD, base_balance=100
    )
    obs = env.reset()

    for i, a in enumerate(actions):
        action = [a]
        obs, reward, done, info = env.step(action)
        rewards.append(reward[0])

    assert round(sum(rewards), 1) == round(tot_expected_reward, 1)
