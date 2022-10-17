from logging import Logger
from pathlib import Path

import pendulum
from attr import define
from cached_property import cached_property
from stable_baselines3 import PPO
from stable_baselines3.common import logger
from stable_baselines3.common.base_class import BaseAlgorithm
from stable_baselines3.common.vec_env import VecNormalize

from repository.db import DataBaseManager, Execution


@define(slots=False)
class ExecutionContext:
    execution: Execution
    db_manager: DataBaseManager
    env: VecNormalize
    logger: Logger

    @property
    def exec_id(self) -> str:
        return str(self.execution.id)

    @cached_property
    def output_dir(self) -> Path:
        return Path(self.execution.output_dir)

    @property
    def logs_path(self) -> str:
        return str(self.output_dir / self.exec_id / "logs/")

    @cached_property
    def model_path(self) -> Path:
        value = self.output_dir / self.exec_id / "model/PPO"
        value.parent.mkdir(parents=True, exist_ok=True)  # Create dir if it doesn't exist
        return value

    @cached_property
    def model(self) -> BaseAlgorithm:
        if self.execution.settings.load_from_execution_id is None:
            self.logger.info("Training model from scratch.")
            return PPO("MultiInputPolicy", self.env, verbose=1)
        else:
            self.logger.info(f"Loading model from path: {self.execution.load_model_path}.")
            return PPO.load(self.execution.load_model_path, env=self.env)

    def train(self) -> None:
        self.logger.info(f"Execution context: {self.execution}")

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
