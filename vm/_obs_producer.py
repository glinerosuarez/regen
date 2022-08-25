import asyncio
import logging

import threading
from queue import Queue
from typing import Optional, Iterator

import pendulum
import numpy as np

import configuration
import log
from repository.remote import BinanceClient
from repository import Interval, TradingPair
from repository.db import DataBaseManager, Kline, get_db_async_generator


class KlineProducer(threading.Thread):
    """Provide klines from the database (if there are any) and the api."""

    # TODO: test that kline values don't differ after some time
    _BUFFER_SIZE = 3

    def __init__(self, trading_pair: TradingPair, daemon: bool = True):
        super(KlineProducer, self).__init__(daemon=daemon)

        now = pendulum.now()
        self.trading_pair = trading_pair
        self.queue = Queue(self._BUFFER_SIZE)  # interface to expose klines to the main thread
        self._api_queue = asyncio.Queue(self._BUFFER_SIZE)  # buffer for klines that come directly from the api
        self.db_manager = DataBaseManager
        self.client = BinanceClient()
        self.last_stime = now.subtract(minutes=1).start_of("minute")  # we will start getting klines from this minute
        self.last_etime = now.subtract(minutes=1).end_of("minute")
        self.background_tasks = set()
        self.logger = log.LoggerFactory.get_console_logger(__name__, logging.DEBUG)

    async def get_pending(self):
        """
        Get the klines from the api, it is meant to get the kline from the last elapsed minute, though it will also get
        missed klines.
        """
        # Define the kline period (start and end to get data from and to)
        period = pendulum.period(self.last_stime.add(minutes=1), pendulum.now().start_of("minute"))
        kl_times = [t for t in period.range("minutes")]
        stime = kl_times[0]
        etime = kl_times[-1].end_of("minute")

        klines = self.client.get_klines_data(
            self.trading_pair, Interval.M_1, start_time=stime, end_time=etime, limit=len(kl_times)
        )

        self.last_stime = stime  # keep track of the last kline produced, the next kline will be the kline corresponding
        self.last_etime = etime  # to the next minute.

        for kl in klines:
            await self._api_queue.put(kl)  # store in buffer

    async def schedule_job(self):
        """Trigger kline acquisition coroutine every minute at the 59th second."""
        now = pendulum.now()
        next_job = now.at(now.hour, now.minute, 59)
        wait_time = pendulum.now().diff(next_job).total_seconds()  # Approx time from now to the next execution
        while True:
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            await self.get_pending()

            next_job = next_job.add(minutes=1)
            wait_time = pendulum.now().diff(next_job).total_seconds()  # seconds to wait for the next run

    async def main(self):
        """Main coroutine to coordinate klines production."""
        schedule_task = asyncio.create_task(self.schedule_job())  # Start getting klines from the api
        self.background_tasks.add(schedule_task)  # Create strong reference of the tasks

        # TODO: This will return all the klines records in the database regardless of their trading pair.
        async for db_kline in get_db_async_generator(configuration.settings.db_name, Kline, self._BUFFER_SIZE):
            self.queue.put(db_kline)

        while True:  # Get klines from api
            self.queue.put(await self._api_queue.get())

    def run(self):
        asyncio.run(self.main())

    def get_klines(self) -> Iterator[Kline]:
        """Return a generator that produces klines as they are available."""
        while True:
            yield self.queue.get()


class ObsProducer:
    _OBS_TYPE = "float32"
    _KLINE_FEATURES = 5

    def __init__(self, trading_pair: TradingPair, window_size: int):
        self.window_size = window_size
        self.logger = log.LoggerFactory.get_console_logger(__name__)

        self.producer = KlineProducer(trading_pair)
        if not self.producer.is_alive():
            self.producer.start()

        self.chunks_generator = self.get_kline_chunk()
        self.next_chunk = None

    def get_kline_chunk(self) -> Iterator[Optional[np.ndarray]]:
        """A generator that yields chunks of klines."""

        def get_empty_chunk() -> np.ndarray:
            return np.zeros((self.window_size, self._KLINE_FEATURES + 1))  # The ´+ 1´ is to keep track of the open time

        def kline_to_np(kline: Kline) -> np.ndarray:
            return np.array((kline.open_value, kline.high, kline.low, kline.close_value, kline.volume, kline.open_time))

        kl_generator = self.producer.get_klines()
        chunk = get_empty_chunk()
        chunk[0, :] = kline_to_np(next(kl_generator))  # insert first kline into the chunk
        chunk_size = 1

        for kl in kl_generator:
            if chunk[chunk_size - 1][-1] == kl.open_time - 60_000:  # then we check that this is a subsequent kline
                if chunk_size == self.window_size:  # if the chunk has already been delivered
                    chunk = np.roll(chunk, -1, axis=0)  # shift up to only keep the most recent window_size - 1 klines
                    chunk[-1, :] = kline_to_np(kl)  # we add the kline to the last row of the chunk
                else:  # if it has not
                    chunk[chunk_size, :] = kline_to_np(kl)  # we add to the corresponding position in the chunk
                    chunk_size += 1
            else:  # if it is not
                chunk = get_empty_chunk()  # we discard this chunk
                chunk[0, :] = kline_to_np(kl)  # and start populating a new one
                chunk_size = 1
                yield None  # yield None to send a signal that this was a failed chunk :(
            # yield chunk if complete, remove the last column (open time) that we use to check that kl's are subsequent
            if chunk_size == self.window_size:
                yield chunk[:, :-1].astype(self._OBS_TYPE)

    def get_observation(self) -> tuple[np.ndarray, Optional[bool]]:
        """
        Deliver an observation either from the database or a new one from the api.
        :return: Observation data and a flag to identify the end of an episode, which in this case occurs when there is
            a time gap between klines.
        """
        while self.next_chunk is None:  # request a new chunk until we get a valid one
            self.next_chunk = next(self.chunks_generator)

        this_chunk = self.next_chunk  # ok it's time for next_chunk to shine
        self.next_chunk = next(self.chunks_generator)  # and someone else must fill that place

        if self.next_chunk is None:  # but we've got a potential problem, next chunk could be erroneous
            done = True  # in this case we need to send a signal to finish the episode
        else:
            done = False  # if it is not, then everything is good!
        return this_chunk, done
