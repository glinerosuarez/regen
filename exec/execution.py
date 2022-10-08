from pathlib import Path

import pendulum
from attr import define
from stable_baselines3 import PPO
from stable_baselines3.common import logger
from stable_baselines3.common.vec_env import VecNormalize

from repository import TradingPair
from repository.db import DataBaseManager, Execution
from vm.crypto_vm import CryptoViewModel


@define
class ExecutionContext:

    pair: TradingPair
    db_manager: DataBaseManager
    execution: Execution
    exec_id: str
    vm: CryptoViewModel
    env: VecNormalize
    output_dir: Path
    time_steps: int

    @property
    def logs_path(self) -> str:
        return str(self.output_dir / self.exec_id / "logs/")

    def train(self) -> None:
        try:
            # set up logger
            train_logger = logger.configure(self.logs_path, ["stdout", "csv", "tensorboard"])
            model = PPO("MultiInputPolicy", self.env, verbose=1)
            model.set_logger(train_logger)
            model.learn(total_timesteps=self.time_steps)
        finally:
            model_path = self.output_dir / self.exec_id / "model/PPO"
            model_path.parent.mkdir(parents=True, exist_ok=True)  # Create dir if it doesn't exist
            model.save(model_path)

            env_path = self.output_dir / self.exec_id / "env/env.pkl"
            env_path.parent.mkdir(parents=True, exist_ok=True)  # Create dir if it doesn't exist
            self.env.save(str(env_path))

            self.execution.end = pendulum.now().timestamp()  # Register execution end time
            self.db_manager.session.commit()

    def train_in_live_mode(self):
        # env = load_crypto_trading_env(conf.settings.path_to_env_stats, self.vm)
        pass
