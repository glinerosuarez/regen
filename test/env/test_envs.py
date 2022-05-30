from stable_baselines3.common.env_checker import check_env

from consts import CryptoAsset
from env import CryptoTradingEnv


def test_cryptoenv():
    # WARNING: since the minimum observation frequency is 1 min, this will take several minutes to run.
    env = CryptoTradingEnv(window_size=5, base_asset=CryptoAsset.BNB, quote_asset=CryptoAsset.BUSD, base_balance=100)
    check_env(env)
