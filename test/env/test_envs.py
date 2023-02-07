from stable_baselines3.common.env_checker import check_env

import conf
from conf.consts import CryptoAsset
from env import build_crypto_trading_env
from env._envs import CryptoTradingEnv


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


# def test_cryptoenv(insert_klines, vm):
# TODO: Fix this test, it requires mocking an observation table.
# env = CryptoTradingEnv(vm)
# check_env(env)
# _execute_steps(env)
