import itertools
import logging

import threading
from dataclasses import dataclass
from queue import Queue
from typing import Optional, Iterator, Tuple

import numpy as np

from repository.db import DataBaseManager
from repository.db.utils import get_table_generator


@dataclass
class ObsData:
    kline_id: int
    open_value: float
    high: float
    low: float
    close_value: float
    ma_7: float
    ma_25: float
    ma_100: float
    ma_300: float
    ma_1440: float
    ma_14400: float
    ma_144000: float
    open_ts: int

    def to_array(self) -> np.ndarray:
        return np.array(
            (
                self.open_value,
                self.high,
                self.low,
                self.close_value,
                self.ma_7,
                self.ma_25,
                self.ma_100,
                self.ma_300,
                self.ma_1440,
                self.ma_14400,
                self.ma_144000,
                self.open_ts,
            )
        )


class ObsDataProducer(threading.Thread):
    """Provide klines from the database."""

    def __init__(
        self,
        db_manager: DataBaseManager,
        table: str,
        logger: logging.Logger,
        schema: Optional[str] = None,
        enable_live_mode: bool = False,
        buffer_size: int = 10_000,
        daemon: bool = True,
    ):
        super(ObsDataProducer, self).__init__(daemon=daemon)

        self.table = table
        self.schema = schema
        self.db_manager = db_manager
        self.logger = logger

        self.enable_live_mode = enable_live_mode  # True to continuously request new obs data
        self.buffer_size = buffer_size
        self.queue = Queue(buffer_size)  # interface to expose obs data to the main thread

    def run(self):
        if self.enable_live_mode is True:
            self.logger.info("Live mode is enabled.")
            raise NotImplementedError

        for obs_data in get_table_generator(
            self.db_manager, table=self.table, schema=self.schema, page_size=self.buffer_size
        ):
            self.queue.put(ObsData(*obs_data))

    def get_obs_data(self) -> Iterator[ObsData]:
        """Return a generator that produces klines as they are available."""

        def get_data_counter() -> Iterator[None]:
            n_rows = self.db_manager.execute_count_rows(table=self.table, schema=self.schema)
            self.logger.info(f"Returning {n_rows} rows.")
            return itertools.repeat(None, n_rows)

        for _ in get_data_counter():
            yield self.queue.get()


class ObsProducer:
    _OBS_TYPE = "float32"

    def get_obs_chunk(self) -> Iterator[Optional[np.ndarray]]:
        """A generator that yields chunks of obs data."""

        def get_empty_chunk() -> np.ndarray:
            return np.zeros((self.window_size, self.n_features + 1))  # The ´+ 1´ is to keep track of the open time

        obs_data_generator = self.producer.get_obs_data()
        chunk = get_empty_chunk()
        chunk[0, :] = next(obs_data_generator).to_array()  # insert first obs data into the chunk
        chunk_size = 1

        for od in obs_data_generator:
            self.logger.debug(f"Got observation data {od} from obs data producer.")
            if chunk[chunk_size - 1][-1] == od.open_ts - 60_000:  # then we check that this is a subsequent kline
                if chunk_size == self.window_size:  # if the chunk has already been delivered
                    chunk = np.roll(chunk, -1, axis=0)  # shift up to only keep the most recent window_size - 1 obs data
                    chunk[-1, :] = od.to_array()  # we add the obs data to the last row of the chunk
                else:  # if it has not
                    chunk[chunk_size, :] = od.to_array()  # we add to the corresponding position in the chunk
                    chunk_size += 1
            else:  # if it is not
                chunk = get_empty_chunk()  # we discard this chunk
                chunk[0, :] = od.to_array()  # and start populating a new one
                chunk_size = 1
                yield None  # yield None to send a signal that this was a failed chunk :(
            # yield chunk if complete, remove the last column (open time) that we use to check that data is subsequent
            if chunk_size == self.window_size:
                yield chunk[:, :-1].astype(self._OBS_TYPE)

    def __init__(self, obs_data_prod: ObsDataProducer, window_size: int, n_features: int, logger: logging.Logger):
        self.window_size = window_size
        self.n_features = n_features
        self.logger = logger

        self.producer = obs_data_prod
        if not self.producer.is_alive():
            self.producer.start()

        self.chunks_generator = self.get_obs_chunk()
        self.next_chunk = None

    def get_observation(self) -> Tuple[np.ndarray, Optional[bool]]:
        """
        Deliver an observation.
        :return: Observation data and a flag to identify the end of an episode, which in this case occurs when there is
            a time gap between observations.
        """
        # TODO: trigger StopIteration when there isn't data
        while self.next_chunk is None:  # request a new chunk until we get a valid one
            self.next_chunk = next(self.chunks_generator)

        this_chunk = self.next_chunk  # ok it's time for next_chunk to shine
        self.next_chunk = next(self.chunks_generator)  # and someone else must fill that place

        if self.next_chunk is None:  # but we've got a potential problem, next chunk could be erroneous
            done = True  # in this case we need to send a signal to finish the episode
        else:
            done = False  # if it is not, then everything is good!
        return this_chunk, done
