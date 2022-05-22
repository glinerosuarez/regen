import subprocess
from typing import Generic
from collections import defaultdict
from abc import ABC, abstractmethod
from functools import cached_property

import time
import threading
import numpy as np
from queue import Queue

import config
import log
from repository import Interval
from consts import CryptoAsset, Side
from repository.db import DataBaseManager
from repository.db._db_manager import EnvState, Observation
from vm.consts import E, Action, Position
from repository.remote import BinanceClient
from repository._dataclass import TradingPair


class FixedFrequencyProducer(threading.Thread, ABC, Generic[E]):

    DEFAULT_FREQ = 60

    def __init__(self, queue: Queue[E], frequency: int = DEFAULT_FREQ, daemon: bool = True):
        super(FixedFrequencyProducer, self).__init__(daemon=daemon)
        self.queue = queue
        self.frequency = frequency
        self.logger = log.LoggerFactory.get_console_logger(__name__)

    @abstractmethod
    def _get_element(self) -> E:
        raise NotImplementedError

    def run(self):
        while True:
            if not self.queue.full():
                element = self._get_element()
                self.queue.put(element)
                self.logger.debug(f"Putting {element} : {self.queue.qsize()} elements in queue.")
                time.sleep(self.frequency)


class KlinesProducer(FixedFrequencyProducer):
    _MAX_QUEUE_SIZE = 10

    def __init__(self, trading_pair: TradingPair, n_klines):
        super().__init__(queue=Queue(self._MAX_QUEUE_SIZE))
        # Client to query the data.
        self.client = BinanceClient()
        self.trading_pair = trading_pair
        self.n_klines = n_klines

    def _get_element(self) -> E:
        return self.client.get_klines_data(self.trading_pair, Interval.M_1, limit=self.n_klines)


class CryptoViewModel:

    _TICKS_PER_EPISODE = 60  # at 1 tick per second, this means that an episode last 1 hour at most.

    def __init__(
        self,
        base_asset: CryptoAsset,
        quote_asset: CryptoAsset,
        window_size: int,
        base_balance: float = 0,
        quote_balance: float = 0,
        trade_fee_ask_percent: float = 0.0,
        trade_fee_bid_percent: float = 0.0,
    ):
        """
        :param base_asset: The crypto asset we want to accumulate.
        :param quote_asset: The crypto asset we trade our main asset against.
        :param window_size: Number of ticks (current and previous ticks) returned as an observation.
        """
        if not base_balance and not quote_balance:
            raise ValueError("Both base_balance and quote_balance are equal to zero, you need assets to create the env")

        self.base_asset = base_asset
        self.quote_asset = quote_asset
        self.trading_pair = TradingPair(base_asset, quote_asset)
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

        self.episode_id = None
        self.producer = KlinesProducer(TradingPair(base_asset, quote_asset), window_size)
        self.position = Position.Short
        self.start_tick = window_size
        self.current_tick = None
        self.total_reward = 0.0
        self.total_profit = None
        self.done = None
        self.position_history = (self.window_size * [None]) + [self.position]
        self.history = defaultdict(list)
        self.client = BinanceClient()
        self.last_price = None
        self.last_trade_price = None
        self.logger = log.LoggerFactory.get_console_logger(__name__)

        DataBaseManager.init_connection(config.settings.db_name)
        DataBaseManager.create_all()

    def reset(self):
        if not self.producer.is_alive():
            self.producer.start()

        self.done = False
        self.current_tick = self.window_size

        # We always start longing
        if self.base_balance > self.quote_balance:
            self._place_order(Side.SELL)

        self.position = Position.Long
        self.position_history = (self.window_size * [None]) + [self.position]
        self.total_reward = 0.0
        self.last_price = None
        self.last_trade_price = None

        self.episode_id = self._get_episode_id()
        return self._get_observation()

    def step(self, action: Action):
        self.done = False
        self.current_tick += 1

        # TODO: for now, an episode has a fixed length of _TICKS_PER_EPISODE ticks.
        if self.current_tick == self._TICKS_PER_EPISODE:
            self.done = True

        step_reward = self._calculate_reward(action)
        self.total_reward += step_reward

        self.position_history.append(self.position)
        observation = self._get_observation()
        info = dict(total_reward=self.total_reward, total_profit=self.total_profit, position=self.position.value)
        self._update_history(info)

        return observation, step_reward, self.done, info

    @cached_property
    def execution_id(self) -> int:
        last_exec_id = DataBaseManager.select_max(EnvState.execution_id)
        return last_exec_id + 1 if last_exec_id is not None else 0

    def _get_episode_id(self) -> int:
        last_ep_id = DataBaseManager.select_max(EnvState.episode_id, EnvState.episode_id == self.execution_id)
        return last_ep_id + 1 if last_ep_id is not None else 0

    def _is_trade(self, action: Action):
        return any(
            [
                action == Action.Buy and self.position == Position.Short,
                action == Action.Sell and self.position == Position.Long,
            ]
        )

    def _get_observation(self):
        while True:
            if self.producer.is_alive():
                if self.producer.queue.empty():
                    time.sleep(self.producer.DEFAULT_FREQ / 2)
                    continue
                else:
                    obs_data = self.producer.queue.get()
                    self.logger.debug(f"Getting {obs_data} : {self.producer.queue.qsize()} elements in queue.")
                    self.logger.debug(f"Saving observation in database.")
                    DataBaseManager.insert(
                        Observation(
                            execution_id=self.execution_id,
                            episode_id=self.episode_id,
                            klines=obs_data,
                            ts=time.time(),
                        )
                    )
                    return np.array(  # Return observation as a numpy array because everybody uses numpy.
                        [np.array([kl.open_value, kl.high, kl.low, kl.close_value, kl.volume]) for kl in obs_data]
                    )

    def _calculate_reward(self, action: Action):
        step_reward = 0

        if self._is_trade(action):
            quantity, self.last_price = self._place_order(Side.BUY if action == Action.Buy else Side.SELL)

            if self.position == Position.Short:  # Our objective is to accumulate the base.
                step_reward = self.last_trade_price - self.last_price

            self.last_trade_price = self.last_price  # Update last trade price

            self._store_env_state_data(action, is_trade=True)
            self._update_balances(action, quantity, self.last_price)

            self.position = self.position.opposite()
        else:
            self.last_price = self._get_price()
            self._store_env_state_data(action, is_trade=False)

        return step_reward

    def _store_env_state_data(self, action: Action, is_trade: bool) -> None:
        DataBaseManager.insert(
            EnvState(
                execution_id=self.execution_id,
                episode_id=self.episode_id,
                tick=self.current_tick,
                price=self.last_price,
                position=self.position,
                action=action,
                is_trade=is_trade,
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

    def _place_order(self, side: Side) -> tuple[float, float]:
        # order = self.client.place_order(
        #    pair=self.trading_pair,
        #    side=side,
        #    type=OrderType.MARKET,
        #    quantity=self.balance,
        #    new_client_order_id=self.execution_id
        # )
        # TODO: Get trade price.
        # TODO: To train the initial agent we can skip placing a real order and use the curent price instead.
        # The price and quantity will be returned by client.place_order.
        price = self.client.get_price(self.trading_pair)
        if side == Side.BUY:
            quantity = self.quote_balance * (1 - self.trade_fee_bid_percent) / price
        else:
            quantity = self.base_balance * (1 - self.trade_fee_ask_percent)
        return quantity, price

    def _get_price(self):
        return self.client.get_price(self.trading_pair)
