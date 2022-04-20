import numpy as np
import time
import threading
from abc import ABC, abstractmethod
from queue import Queue
from typing import TypeVar, Generic

from attr import define, field

import log
from consts import CryptoAsset
from repository import Interval
from repository._dataclass import TradingPair
from repository.remote import BinanceClient


E = TypeVar("E")


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
    def __init__(self, base_asset: CryptoAsset, quote_asset: CryptoAsset, window_size: int):
        """
        :param base_asset: The crypto asset we want to accumulate.
        :param quote_asset: The crypto asset we trade our main asset against.
        :param window_size: Number of ticks (current and previous ticks) returned as an observation.
        """
        self.base_asset = base_asset
        self.quote_asset = quote_asset
        self.window_size = window_size
        self.producer = KlinesProducer(TradingPair(base_asset, quote_asset), window_size)
        self.logger = log.LoggerFactory.get_console_logger(__name__)

    def reset(self):
        if not self.producer.is_alive():
            self.producer.start()

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

