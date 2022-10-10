from logging import Logger
from pathlib import Path

import pendulum
from attr import define
from cached_property import cached_property
from stable_baselines3 import PPO
from stable_baselines3.common import logger
from stable_baselines3.common.base_class import BaseAlgorithm
from stable_baselines3.common.vec_env import VecNormalize

from log import LoggerFactory
from repository.db import DataBaseManager, Execution
from vm.crypto_vm import CryptoViewModel


@define(slots=False)
class ExecutionContext:
    execution: Execution
    db_manager: DataBaseManager
    vm: CryptoViewModel
    env: VecNormalize
    output_dir: Path

    @property
    def exec_id(self) -> str:
        return str(self.execution.id)

    @property
    def logs_path(self) -> str:
        return str(self.output_dir / self.exec_id / "logs/")

    @cached_property
    def logger(self) -> Logger:
        return LoggerFactory.get_file_logger(__name__, Path(self.logs_path))

    @cached_property
    def model_path(self) -> Path:
        value = self.output_dir / self.exec_id / "model/PPO"
        value.parent.mkdir(parents=True, exist_ok=True)  # Create dir if it doesn't exist
        return value

    @cached_property
    def model(self) -> BaseAlgorithm:
        if self.execution.settings.load_from_execution_id is None:
            self.logger.info(f"Training model from scratch.")
            return PPO("MultiInputPolicy", self.env, verbose=1)
        else:
            self.logger.info(f"Loading model from path: {self.model_path}.")
            return PPO.load(self.execution.load_model_path, env=self.env)

    def train(self) -> None:
        try:
            # set up logger
            train_logger = logger.configure(self.logs_path, ["stdout", "csv", "tensorboard"])
            self.model.set_logger(train_logger)
            self.model.learn(total_timesteps=self.execution.n_steps)
        finally:
            self.model.save(self.model_path)
            env_path = self.output_dir / self.exec_id / "env/env.pkl"
            env_path.parent.mkdir(parents=True, exist_ok=True)  # Create dir if it doesn't exist
            self.env.save(str(env_path))

            self.execution.end = pendulum.now().timestamp()  # Register execution end time
            self.db_manager.session.commit()
