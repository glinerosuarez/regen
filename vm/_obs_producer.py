import asyncio
import logging

import time
import threading
from queue import Queue
from typing import Optional, Iterator

import pendulum
import numpy as np

import configuration
import log
from repository.remote import BinanceClient
from repository import Interval, TradingPair, Observation
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
            self.trading_pair,
            Interval.M_1,
            start_time=stime,
            end_time=etime,
            limit=len(kl_times)
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

    def __init__(self, trading_pair: TradingPair, window_size: int, execution_id: int, use_db_buffer: bool = True):
        self.window_size = window_size
        self.use_db_buffer = use_db_buffer  # Deliver observations from the database or not
        self.execution_id = execution_id
        self.logger = log.LoggerFactory.get_console_logger(__name__)

        self.producer = KlineProducer(trading_pair)
        if not self.producer.is_alive():
            self.producer.start()

    def get_kline_chunk(self) -> Iterator[Optional[np.ndarray]]:
        """A generator that yields chunks of klines."""

        def get_empty_chunk() -> np.ndarray:
            return np.zeros((self.window_size, self._KLINE_FEATURES + 1))  # The ´+ 1´ is to keep track of the open time

        def kline_to_np(kline: Kline) -> np.ndarray:
            return np.array((kline.open_value, kline.high, kline.low, kline.close_value, kline.volume, kline.open_time))

        chunk = get_empty_chunk()
        i = 0

        for kl in self.producer.get_klines():
            if i == 0:  # If this is the first kline in the chunk we just simply add it
                chunk[i, :] = kline_to_np(kl)
                i += 1
            else:  # if it is not
                if chunk[i - 1][-1] == kl.open_time - 60_000:  # then we check that this is a subsequent kline
                    chunk[i, :] = kline_to_np(kl)  # if it is we add it to the chunk
                    i += 1
                else:  # if it is not then we discard this chunk and return None
                    chunk = get_empty_chunk()
                    i = 0
                    yield None

            if i == self.window_size:  # yield the chunk if complete
                i = 0
                yield chunk[:, :-1]  # Remove the last column (open time) that we use to check that kl's are subsequent

    def get_observation(self, episode_id: int) -> tuple[np.ndarray, Optional[bool]]:
        """
        Deliver an observation either from the database or a new one from the api.
        :return: Observation data and a flag to identify the end of an episode.
        """

        def klines_to_numpy(klines: list[Kline]):
            return np.array(  # Return observation as a numpy array because everybody uses numpy.
                [np.array([kl.open_value, kl.high, kl.low, kl.close_value, kl.volume]) for kl in klines]
            ).astype(self._OBS_TYPE)

        if (obs := self.next_observation) is not None and self.use_db_buffer:
            self.logger.debug(f"Serving {obs=} from database.")
            self.next_observation = next(self.db_buffer, None)
            return (
                klines_to_numpy(obs.klines),
                (
                    # If there's no next obs then this is the last obs in the db and an episode end,
                        self.next_observation is None
                        or
                        # if the execution_id is different in the next obs then this is the last obs in this episode.
                        obs.execution_id != self.next_observation.execution_id
                        or
                        # if the episode_id is different in the next obs then this is the last obs in this episode.
                        obs.episode_id != self.next_observation.episode_id
                ),
            )
        else:
            while True:
                if self.producer.is_alive():
                    if self.producer.queue.empty():
                        time.sleep(self.producer.frequency / 2)
                        continue
                    else:
                        obs_data = self.producer.queue.get()
                        self.logger.debug(f"Getting {obs_data} : {self.producer.queue.qsize()} elements in queue.")
                        self.logger.debug("Saving observation in database.")
                        DataBaseManager.insert(
                            Observation(execution_id=self.execution_id, episode_id=episode_id, klines=obs_data)
                        )
                        return klines_to_numpy(obs_data), False
