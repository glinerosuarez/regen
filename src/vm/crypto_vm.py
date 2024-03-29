import time
import random
from logging import Logger
from typing import Optional

import numpy as np

from conf.consts import Position, Side, Action
from vm._obs_producer import ObsProducer
from repository.db import DataBaseManager
from repository.remote import BinanceClient, OrderData
from repository import EnvState, TradingPair


class CryptoViewModel:
    TRADE_FEE_PERCENTAGE = 0.001  # EXPERIMENTAL

    def __init__(
        self,
        trading_pair: TradingPair,
        db_manager: DataBaseManager,
        api_client: BinanceClient,
        obs_producer: ObsProducer,
        ticks_per_episode: int,
        execution_id: str,
        window_size: int,
        train_mode: bool,
        logger: Logger,
        base_balance: float = 10,
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

        self.train_mode = train_mode

        # Number of ticks (current and previous ticks) returned as an observation.
        self.window_size = window_size
        self.init_base_balance = base_balance
        self.base_balance = base_balance
        self.quote_balance = quote_balance
        # The ask price represents the minimum price that a seller is willing to take for that same security, so this is
        # the fee the exchange charges for buying.
        self.trade_fee_ask_percent = trade_fee_ask_percent
        # The bid price represents the maximum price that a buyer is willing to pay for a share of stock or other
        # security, so this is the fee the exchange charges for buying.
        self.trade_fee_bid_percent = trade_fee_bid_percent

        self.db_manager = db_manager
        self.api_client = api_client
        self.obs_producer = obs_producer
        self.place_orders = place_orders

        self.episode_id = None
        self.position = None
        self.start_tick = window_size
        self.current_tick = None
        self.total_reward = 0.0
        self.done = None
        self.last_observation = None
        self.last_price = None
        self.last_trade_price = None
        self.init_price = None

        self.logger = logger

    @property
    def next_env_state_id(self) -> int:
        last_id = self.db_manager.get_last_id(EnvState)
        return 0 if last_id is None else last_id + 1

    @property
    def last_episode_id(self) -> Optional[int]:
        """Get the last episode id in this execution, return None if there's no last episode id."""
        return self.db_manager.select_max(col=EnvState.episode_id, condition=EnvState.execution_id == self.execution_id)

    def normalize_obs(self, obs: np.ndarray) -> np.ndarray:
        """Flatten and normalize an observation"""
        obs = obs.copy()  # it's ok to shallow copy because we only store doubles, and I don't think that will change
        # The initial price is the last price in the first observation
        if self.init_price is None:  # This should only happen when in the beginning of a new episode
            self.init_price = random.uniform(obs[-2][0], obs[-2][3])  # random value between open and close values
        # TODO: does this break markov rules?
        # Normalize prices by computing the percentual change between the prices in the obs and the last trade price
        non_null_last_trade_price = self.init_price if self.last_trade_price is None else self.last_trade_price
        prices = ((obs - non_null_last_trade_price) / non_null_last_trade_price).flatten()
        return prices

    def reset(self):
        self.logger.debug("Resetting environment.")

        self.done = False
        self.current_tick = self.window_size

        if self.position is None:
            if self.base_balance > self.quote_balance:
                self.position = Position.Long
            else:
                self.position = Position.Short

        self.total_reward = 0.0
        self.last_price = None if self.last_price is None else self.last_price
        self.last_trade_price = None if self.last_trade_price is None else self.last_trade_price
        self.episode_id = 1 if self.last_episode_id is None else self.last_episode_id + 1
        self.logger.debug(f"Updating episode_id, new value: {self.episode_id}")

        if self.train_mode and self.position == Position.Long:  # to better visualize results during training
            self.base_balance = self.init_base_balance
            self.quote_balance = 0

        # TODO: episodes should have a min num of steps i.e. it doesn't make sense to have an episode with only 2 steps
        self.last_observation, done = self.obs_producer.get_observation()

        return dict(klines=self.normalize_obs(self.last_observation), position=Position.Long.value)

    def step(self, action: Action):
        # TODO: Finish episode if balance goes to 0
        self.done = False

        step_reward = self._calculate_reward(action)
        self.total_reward += step_reward
        self.last_observation, self.done = self.obs_producer.get_observation()
        info = dict(
            total_reward=self.total_reward,
            base_balance=self.base_balance,
            quote_balance=self.quote_balance,
            position=self.position.value,
        )

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
            o_data = self._place_order(Side.BUY if action == Action.Buy else Side.SELL)
            if o_data is not None:  # Successful order placed.
                self.last_price = o_data.price  # Update last price
                self._update_balances(action, o_data)  # Update balances

                if self.position == Position.Short:  # Our objective is to accumulate the base.
                    # We normalize the rewards as percentages, this way, changes in price won't affect the agent's
                    # behavior
                    step_reward = ((self.last_trade_price - self.last_price) / self.last_trade_price) * 100  # pp
                    self.logger.debug(f"Got reward: {step_reward}.")

                self.last_trade_price = self.last_price  # Update last trade price
                self._store_env_state_data(action, step_reward, is_trade=True)
                self.position = self.position.opposite()

                return step_reward

        # No trade was done or unsuccessful order.
        if self.train_mode:  # compute opportunity cost (cost of no action)
            if self.position == Position.Short:
                h_price = self._get_price_training(Side.BUY)
                h_reward = ((self.last_trade_price - h_price) / self.last_trade_price) * 100  # pp
                if h_reward > 0:
                    step_reward -= h_reward
            # else:
            #    if self.last_price > self.last_trade_price * (1 + self.TRADE_FEE_PERCENTAGE):

        self.logger.debug("Saving env state without reward.")
        self.last_price = self._get_price_training() if self.train_mode else self._get_price()
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
                base_balance=self.base_balance,
                quote_balance=self.quote_balance,
                action=action,
                is_trade=is_trade,
                reward=reward,
                cum_reward=reward + self.total_reward,  # TODO: this metric doesn't make sense
                ts=time.time(),
            )
        )

    def _update_balances(self, action: Action, o_data: OrderData) -> None:
        if action == action.Sell:
            self.base_balance = o_data.base_qty
            self.quote_balance = o_data.quote_qty + self.quote_balance
        else:
            self.base_balance = o_data.base_qty + self.base_balance
            self.quote_balance = o_data.quote_qty

    def _place_order(self, side: Side) -> Optional[OrderData]:
        if self.place_orders is True:
            if side == side.BUY:
                self.logger.debug("Placing buy order.")
                return self.api_client.buy_at_market(self.next_env_state_id, self.trading_pair, self.quote_balance)
            else:
                self.logger.debug("Placing sell order.")
                return self.api_client.sell_at_market(self.next_env_state_id, self.trading_pair, self.base_balance)
        else:
            price = self._get_price_training(side)
            # The price and quantity will be returned by client.place_order.
            if side == Side.BUY:
                return OrderData(self.quote_balance * (1 - self.trade_fee_bid_percent) / price, 0, price)
            else:
                return OrderData(0, self.base_balance * price * (1 - self.trade_fee_ask_percent), price)

    def _get_price(self):
        price = self.api_client.get_price(self.trading_pair)
        self.logger.debug(f"Got current price from api: {price}.")
        return price

    def _get_price_training(self, side: Optional[Side] = None) -> float:
        price_fee = 0 if side is None else self.TRADE_FEE_PERCENTAGE
        price = self.last_observation[-1][3]
        if side == Side.BUY:
            price = price * (1 + price_fee)
        else:
            price = price * (1 - price_fee)
        self.logger.debug(f"Returning price: {price} for last_observation: {self.last_observation}")
        return price
