import uuid
from collections import defaultdict
from functools import cached_property

import numpy as np
import time
import threading
from abc import ABC, abstractmethod
from queue import Queue
from typing import Generic

from gym_anytrading.envs import Actions, Positions

import log
from consts import CryptoAsset, Side, OrderType
from repository import Interval
from repository._dataclass import TradingPair
from repository.remote import BinanceClient
from vm.consts import E, Action, Position


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
                self.logger.debug(f'Putting {element} : {self.queue.qsize()} elements in queue.')
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
        klines = self.client.get_klines_data(self.trading_pair, Interval.M_1, limit=self.n_klines)
        return np.array([np.array([kl.open_value, kl.high, kl.low, kl.close_value, kl.volume]) for kl in klines])


class CryptoViewModel:

    _TICKS_PER_EPISODE = 60  # at 1 tick per second, this means that an episode last 1 hour at most.

    def __init__(self, base_asset: CryptoAsset, quote_asset: CryptoAsset, balance: float, window_size: int):
        """
        :param base_asset: The crypto asset we want to accumulate.
        :param quote_asset: The crypto asset we trade our main asset against.
        :param window_size: Number of ticks (current and previous ticks) returned as an observation.
        """
        self.base_asset = base_asset
        self.quote_asset = quote_asset
        self.trading_pair = TradingPair(base_asset, quote_asset)
        self.balance = balance
        self.window_size = window_size
        self.producer = KlinesProducer(TradingPair(base_asset, quote_asset), window_size)
        self.position = Positions.Short
        self.start_tick = window_size
        self.current_tick = None
        self.last_trade_tick = None
        self.total_reward = 0.0
        self.total_profit = None
        self.done = None
        # The ask price represents the minimum price that a seller is willing to take for that same security, so this is
        # the fee the exchange charges for buying.
        self.trade_fee_ask_percent = 0.0
        # The bid price represents the maximum price that a buyer is willing to pay for a share of stock or other
        # security, so this is the fee the exchange charges for buying.
        self.trade_fee_bid_percent = 0.0
        self.position_history = (self.window_size * [None]) + [self.position]
        self.history = defaultdict(list)
        self.client = BinanceClient()
        self.logger = log.LoggerFactory.get_console_logger(__name__)

    @cached_property
    def execution_id(self) -> str:
        return str(uuid.uuid4())

    def is_trade(self, action: Action):
        return any([
            action == Actions.Buy.value and self._position == Positions.Short,
            action == Actions.Sell.value and self._position == Positions.Long,
        ])

    def reset(self):
        if not self.producer.is_alive():
            self.producer.start()

        self._position = Positions.Short

    def get_observation(self):
        while True:
            if self.producer.is_alive():
                if self.producer.queue.empty():
                    time.sleep(self.producer.DEFAULT_FREQ / 2)
                    continue
                else:
                    element = self.producer.queue.get()
                    self.logger.debug(f'Getting {element} : {self.producer.queue.qsize()} elements in queue.')
                    return element

    def calculate_reward(self, action: Action):
        step_reward = 0

        if self.is_trade(action):
            # TODO: Get trade price.
            # TODO: To train the initial agent we can skip placing a real order and use the curent price instead
            order = self.client.place_order(
                pair=self.trading_pair,
                side=Side.BUY if action == Action.Buy else Side.SELL,
                type=OrderType.MARKET,
                quantity=self.balance,
                new_client_order_id=self.execution_id
            )

            current_price = self.client.get_current_avg_price()
            #last_trade_price = self.prices[self._last_trade_tick]
            #price_diff = current_price - last_trade_price

            # Our objective is to accumulate the base.
            #if self._position == Positions.Short:
            #    step_reward += price_diff
            ...
        return step_reward

    def update_profit(self, action):
        if self.is_trade(action) or self.done:
            # TODO: Get trade price
            #current_price = self.prices[self._current_tick]
            #last_trade_price = self.prices[self._last_trade_tick]

            if self.position == Position.Short:
                shares = (self.total_profit * (1 - self.trade_fee_bid_percent)) / last_trade_price
                self.total_profit = (shares * (1 - self.trade_fee_ask_percent)) * current_price

    def update_history(self, info):
        for key, value in info.items():
            self.history[key].append(value)

    def step(self, action: Action):
        self.done = False
        self.current_tick += 1

        # TODO: for now, an episode has a fixed length of _TICKS_PER_EPISODE ticks.
        if self.current_tick == self._TICKS_PER_EPISODE:
            self.done = True

        step_reward = self.calculate_reward(action)
        self.total_reward += step_reward

        self.update_profit(action)

        if self.is_trade(action):
            self.position = self.position.opposite()
            self.last_trade_tick = self.current_tick

        self.position_history.append(self.position)
        observation = self.get_observation()
        info = dict(total_reward=self.total_reward, total_profit=self.total_profit, position=self.position.value)
        self.update_history(info)

        return observation, step_reward, self.done, info

