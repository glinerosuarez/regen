from cached_property import cached_property
import pendulum
from stable_baselines3 import PPO
from stable_baselines3.common import logger

import conf
from env import build_crypto_trading_env
from repository import TradingPair
from repository.db import DataBaseManager, Execution, TrainSettings
from vm.crypto_vm import CryptoViewModel


class ExecutionContext:
    @cached_property
    def db_manager(self) -> DataBaseManager:
        return DataBaseManager(
            conf.settings.db_name,
            DataBaseManager.EngineType.PostgreSQL
            if conf.settings.db_type == "postgres"
            else DataBaseManager.EngineType.SQLite,
            conf.settings.db_host,
            conf.settings.db_user,
            conf.settings.db_password,
            conf.settings.db_file_location,
            conf.settings.output_dir,
        )

    def __init__(self):
        ts = pendulum.now()
        pair = TradingPair(conf.settings.base_asset, conf.settings.quote_asset)

        self._execution = Execution(
            pair=pair,
            algorithm=conf.consts.Algorithm.PPO,
            n_steps=conf.settings.time_steps,
            start=ts.timestamp(),
            settings=TrainSettings(
                db_name=conf.settings.db_name,
                window_size=conf.settings.window_size,
                ticks_per_episode=conf.settings.ticks_per_episode,
                is_live_mode=conf.settings.enable_live_mode,
                klines_buffer_size=conf.settings.klines_buffer_size,
            ),
        )
        self.db_manager.insert(self._execution)
        self.exec_id = str(self._execution.id)

        vm = CryptoViewModel(  # VM to get data from sources.
            base_asset=conf.settings.base_asset,
            quote_asset=conf.settings.quote_asset,
            window_size=conf.settings.window_size,
            db_manager=self.db_manager,
            ticks_per_episode=conf.settings.ticks_per_episode,
            execution_id=self.exec_id,
        )
        self.env = build_crypto_trading_env(vm=vm)

        # set up logger
        logs_path = str(conf.settings.output_dir / self.exec_id / "logs/")
        train_logger = logger.configure(logs_path, ["stdout", "csv", "tensorboard"])

        self.model = PPO("MultiInputPolicy", self.env, verbose=1)
        self.model.set_logger(train_logger)

    def train(self):
        try:
            self.model.learn(total_timesteps=conf.settings.time_steps)
        finally:
            self.model.save(conf.settings.output_dir / self.exec_id / "model/PPO")
            self._execution.end = pendulum.now().timestamp()
            self.db_manager.session.commit()
