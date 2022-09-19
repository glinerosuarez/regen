import pendulum
from stable_baselines3 import PPO
from stable_baselines3.common import logger
from stable_baselines3.common.env_util import make_vec_env

import conf
from env import CryptoTradingEnv
from repository import TradingPair
from repository.db import DataBaseManager, Execution, TrainSettings


class ExecutionContext:
    def __init__(self):
        ts = pendulum.now()
        pair = TradingPair(conf.settings.base_asset, conf.settings.quote_asset)
        self.db_manager = DataBaseManager.init()

        env = CryptoTradingEnv(
            window_size=conf.settings.window_size, base_asset=pair.base, quote_asset=pair.quote, base_balance=100
        )
        self.env = make_vec_env(lambda: env, n_envs=1)

        self._execution = Execution(
            pair=pair,
            algorithm=conf.consts.Algorithm.PPO,
            n_steps=conf.settings.time_steps,
            start=ts.timestamp(),
            settings=TrainSettings(
                db_name=conf.settings.db_name,
                window_size=conf.settings.window_size,
                ticks_per_episode=conf.settings.ticks_per_episode,
                is_live_mode=conf.settings.is_live_mode,
                klines_buffer_size=conf.settings.klines_buffer_size,
            ),
        )
        self.db_manager.insert(self._execution)
        self.exec_id = str(self._execution.id)
        conf.settings.execution_id = self.exec_id

        # set up logger
        logs_path = conf.settings.output_dir / self.exec_id / "logs/"
        train_logger = logger.configure(logs_path, ["stdout", "csv", "tensorboard"])

        self.model = PPO("MultiInputPolicy", env, verbose=1)
        self.model.set_logger(train_logger)

    def train(self):
        self.model.learn(total_timesteps=conf.settings.time_steps)

        self._execution.end = pendulum.now().timestamp()
        self.db_manager.session.commit()

        self.model.save(conf.settings.output_dir / self.exec_id / f"model/PPO")
