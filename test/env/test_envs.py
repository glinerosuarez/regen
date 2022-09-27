from stable_baselines3.common.env_checker import check_env

import conf
from conf.consts import CryptoAsset
from env import build_crypto_trading_env


def _execute_steps(env):
    obs = env.reset()
    print(f"first obs: {obs}")
    print(env.observation_space)
    print(env.action_space)
    print(env.action_space.sample())

    n_steps = 4
    for step in range(n_steps):
        print("Step {}".format(step + 1))
        obs, reward, done, info = env.step(1)
        print("obs=", obs, "reward=", reward, "done=", done)
        env.render()
        if done:
            print("Goal reached!", "reward=", reward)
            env.reset()


def test_cryptoenv():
    # WARNING: since the minimum observation frequency is 1 min, this will take several minutes to run.
    env = build_crypto_trading_env(window_size=5, base_asset=CryptoAsset.BNB, quote_asset=CryptoAsset.BUSD, base_balance=100)
    check_env(env)
    # _execute_steps(env)


if __name__ == "__main__":
    conf.settings.execution_id = 10
    env = build_crypto_trading_env(
        window_size=1_440, base_asset=CryptoAsset.BNB, quote_asset=CryptoAsset.BUSD, base_balance=100
    )
    breakpoint()
    _execute_steps(env)
    # test_observations()
