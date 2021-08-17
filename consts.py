import enum
from collections import namedtuple
from dataclasses import dataclass

from attr import attrs, attrib
from attr.validators import instance_of


class EnvConsts:

    MAX_ACCOUNT_BALANCE = 1000.0

    INITIAL_ACCOUNT_BALANCE = 1.0

    MAX_SHARE_PRICE = 300.0

    MAX_NUM_SHARES = 10.0

    MAX_STEPS = 20000

    LOOKBACK_WINDOW_SIZE = 40


class CryptoAsset(enum.Enum):

    BNB: str = 'BNB'
    ETH: str = 'ETH'
    BTC: str = 'BTC'
    USDT: str = 'USDT'
    BUSD: str = 'BUSD'


@dataclass
class TradingPair:
    base: CryptoAsset
    quote: CryptoAsset

    def to_symbol(self):
        return self.base.value + self.quote.value


@attrs
class KlineRecord:
    pair: TradingPair = attrib(validator=instance_of(TradingPair))
    open_time: int = attrib(converter=int)
    open_value: float = attrib(converter=float)
    high: float = attrib(converter=float)
    low: float = attrib(converter=float)
    close_value: float = attrib(converter=float)
    volume: float = attrib(converter=float)
    close_time: int = attrib(converter=int)
    quote_asset_vol: float = attrib(converter=float)  # Volume measured in the units of the second part of the pair.
    trades: int = attrib(converter=int)
    # Explanation: https://dataguide.cryptoquant.com/market-data/taker-buy-sell-volume-ratio
    taker_buy_base_vol: float = attrib(converter=float)
    taker_buy_quote_vol: float = attrib(converter=float)
