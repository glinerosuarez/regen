import time
import threading
from queue import Queue
from typing import Generic
from abc import ABC, abstractmethod

import log
from vm.consts import E
from repository.remote import BinanceClient
from repository import Interval, TradingPair


class FixedFrequencyProducer(threading.Thread, ABC, Generic[E]):
    def __init__(self, queue: Queue[E], frequency: int, daemon: bool = True):
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
    _DEFAULT_FREQ = 60  # Produce 1 element per this time (in seconds)
    _MAX_QUEUE_SIZE = 10_000

    def __init__(self, trading_pair: TradingPair, n_klines: int, freq: int = _DEFAULT_FREQ):
        super().__init__(queue=Queue(self._MAX_QUEUE_SIZE), frequency=freq)
        # Client to query the data.
        self.client = BinanceClient()
        self.trading_pair = trading_pair
        self.n_klines = n_klines

    def _get_element(self) -> E:
        return self.client.get_klines_data(self.trading_pair, Interval.M_1, limit=self.n_klines)
