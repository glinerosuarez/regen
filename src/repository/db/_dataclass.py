from dataclasses import dataclass

import numpy as np


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
