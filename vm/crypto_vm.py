import time
import random
from typing import Optional, Tuple
from collections import defaultdict

import numpy as np

import log
from conf.consts import Position, Side, Action
from vm._obs_producer import ObsProducer
from repository.db import DataBaseManager
from repository.remote import BinanceClient
from repository import EnvState, TradingPair


class CryptoViewModel:
    def __init__(
        self,
        trading_pair: TradingPair,
        db_manager: DataBaseManager,
        api_client: BinanceClient,
        obs_producer: ObsProducer,
        ticks_per_episode: int,
        execution_id: str,
        window_size: int,
        base_balance: float = 100,
        quote_balance: float = 0,
        trade_fee_ask_percent: float = 0.0,
        trade_fee_bid_percent: float = 0.0,
        place_orders: bool = False,
    ):
        """
        :param base_asset: The crypto asset we want to accumulate.
        :param quote_asset: The crypto asset we trade our main asset against.
        :param window_size: Number of ticks (current and previous ticks) returned as an observation.
        """
        if not base_balance and not quote_balance:
            raise ValueError("Both base_balance and quote_balance are equal to zero, you need assets to create the env")

        self.execution_id = execution_id
        self.ticks_per_episode = ticks_per_episode
        self.trading_pair = trading_pair
        # Number of ticks (current and previous ticks) returned as an observation.
        self.window_size = window_size
        self.base_balance = base_balance
        self.quote_balance = quote_balance
        # The ask price represents the minimum price that a seller is willing to take for that same security, so this is
        # the fee the exchange charges for buying.
        self.trade_fee_ask_percent = trade_fee_ask_percent
        # The bid price represents the maximum price that a buyer is willing to pay for a share of stock or other
        # security, so this is the fee the exchange charges for buying.
        self.trade_fee_bid_percent = trade_fee_bid_percent

        self.db_manager = db_manager
        self.client = api_client
        self.obs_producer = obs_producer
        self.place_orders = place_orders

        self.episode_id = None
        self.position = Position.Short
        self.start_tick = window_size
        self.current_tick = None
        self.total_reward = 0.0
        self.done = None
        self.position_history = (self.window_size * [None]) + [self.position]
        self.history = defaultdict(list)
        self.last_observation = None
        self.last_price = None
        self.last_trade_price = None
        self.init_price = None
        self.logger = log.LoggerFactory.get_console_logger(__name__)

    def normalize_obs(self, obs: np.ndarray) -> np.ndarray:
        """Flatten and normalize an observation"""
        obs = obs.copy()  # it's ok to shallow copy because we only store doubles, and I don't think that will change
        # The initial price is the last price in the first observation
        if self.init_price is None:  # This should only happen when in the beginning of a new episode
            self.init_price = random.uniform(obs[-2][0], obs[-2][3])  # random value between open and close values
        # TODO: does this break markov rules?
        # Normalize prices by computing the percentual change between the prices in the obs and the last trade price
        non_null_last_trade_price = self.last_trade_price if self.last_trade_price is not None else self.init_price
        prices = ((obs[:, :4] - non_null_last_trade_price) / non_null_last_trade_price).flatten()
        return prices

    def reset(self):
        self.logger.debug("Resetting environment.")

        self.done = False
        self.current_tick = self.window_size

        # We always start longing
        if self.base_balance < self.quote_balance:
            self._place_order(Side.SELL)

        self.position = Position.Long
        self.position_history = (self.window_size * [None]) + [self.position]
        self.total_reward = 0.0
        self.last_price = None
        self.last_trade_price = None
        self.episode_id = 1 if self._get_last_episode_id() is None else self._get_last_episode_id() + 1
        self.logger.debug(f"Updating episode_id, new value: {self.episode_id}")

        # TODO: episodes should have a min num of steps i.e. it doesn't make sense to have an episode with only 2 steps
        self.last_observation, done = self.obs_producer.get_observation()

        return dict(klines=self.normalize_obs(self.last_observation), position=Position.Long.value)

    def step(self, action: Action):
        # TODO: Finish episode if balance goes to 0
        # breakpoint()
        self.done = False

        step_reward = self._calculate_reward(action)
        self.total_reward += step_reward

        self.position_history.append(self.position)
        self.last_observation, self.done = self.obs_producer.get_observation()
        info = dict(
            total_reward=self.total_reward,
            base_balance=self.base_balance,
            quote_balance=self.quote_balance,
            position=self.position.value,
        )
        self._update_history(info)

        # TODO: for now, an episode has a fixed length of _TICKS_PER_EPISODE ticks.
        self.current_tick += 1
        if self.current_tick >= self.ticks_per_episode:
            self.done = True

        return (
            dict(klines=self.normalize_obs(self.last_observation), position=self.position.value),
            step_reward,
            self.done,
            info,
        )

    def _get_last_episode_id(self) -> Optional[int]:
        """Get the last episode id in this execution, return None if there's no last episode id."""
        return self.db_manager.select_max(col=EnvState.episode_id, condition=EnvState.execution_id == self.execution_id)

    def _is_trade(self, action: Action):
        return any(
            [
                action == Action.Buy and self.position == Position.Short,
                action == Action.Sell and self.position == Position.Long,
            ]
        )

    def _calculate_reward(self, action: Action):
        step_reward = 0.0
        if self._is_trade(action):
            quantity, self.last_price = self._place_order(Side.BUY if action == Action.Buy else Side.SELL)

            if self.position == Position.Short:  # Our objective is to accumulate the base.
                # We normalize the rewards as percentages, this way, changes in price won't affect the agent's behavior
                step_reward = ((self.last_trade_price - self.last_price) / self.last_trade_price) * 100  # pp

            self.last_trade_price = self.last_price  # Update last trade price

            self._store_env_state_data(action, step_reward, is_trade=True)
            self._update_balances(action, quantity, self.last_price)

            self.position = self.position.opposite()
        else:
            self.last_price = self._get_price()
            self._store_env_state_data(action, step_reward, is_trade=False)

        return step_reward

    def _store_env_state_data(self, action: Action, reward: float, is_trade: bool) -> None:
        self.db_manager.insert(
            EnvState(
                execution_id=self.execution_id,
                episode_id=self.episode_id,
                tick=self.current_tick,
                price=self.last_price,
                position=self.position,
                action=action,
                is_trade=is_trade,
                reward=reward,
                cum_reward=reward + self.total_reward,
                ts=time.time(),
            )
        )

    def _update_balances(self, action: Action, quantity: float, price: float) -> None:
        if self._is_trade(action) or self.done:
            if action == Action.Buy:
                self.base_balance = quantity
                self.quote_balance = 0.0
            else:
                self.base_balance = 0.0
                self.quote_balance = quantity * price

    def _update_history(self, info):
        for key, value in info.items():
            self.history[key].append(value)

    def _place_order(self, side: Side) -> Tuple[float, float]:
        if self.place_orders is True:
            # order = self.client.place_order(
            #    pair=self.trading_pair,
            #    side=side,
            #    type=OrderType.MARKET,
            #    quantity=self.balance,
            #    new_client_order_id=self.execution_id
            # )
            pass
        else:
            price = self._get_price()
            # The price and quantity will be returned by client.place_order.
            if side == Side.BUY:
                quantity = self.quote_balance * (1 - self.trade_fee_bid_percent) / price
            else:
                quantity = self.base_balance * (1 - self.trade_fee_ask_percent)
            return quantity, price

    def _get_price(self):
        price = self.last_observation[-1][3]
        self.logger.debug(f"Returning price: {price} for last_observation: {self.last_observation}")
        return price
