from pathlib import Path
from typing import List


from conf.consts import Action
from repository import EnvState
from repository.db import DataBaseManager, Execution


if __name__ == '__main__':
    execution_id = "1"
    db_manager = DataBaseManager(db_name="regen_latest", files_dir=Path()/"tmp")
    exec_data: Execution = db_manager.select(Execution, Execution.id == execution_id)[0]
    cum_reward = 0
    base_balance = 1
    quote_balance = 0

    last_episode_data: List[EnvState] = db_manager.select(EnvState, EnvState.episode_id == 355)

    for state in last_episode_data:
        if state.is_trade:
            if state.action == Action.Buy:
                base_balance = quote_balance / state.price
                quote_balance = 0
            if state.action == Action.Sell:
                quote_balance = base_balance * state.price
                base_balance = 0
