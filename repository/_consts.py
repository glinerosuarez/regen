from datetime import datetime
from enum import Enum
from typing import List, Dict, Any

import utils
from consts import TradingPair, TimeInForce, OrderType, Side, CryptoAsset
from attr import attrs, attrib
from attr.validators import instance_of


class Interval(Enum):
    M_1 = '1m'
    M_5 = '5m'
    H_1 = '1h'
    D_1 = '1d'

@attrs
class Fill:
    price: float = attrib(converter=float)
    qty: float = attrib(converter=float)
    commission: float = attrib(converter=float)
    commissionAsset: CryptoAsset = attrib(converter=CryptoAsset.__getitem__)

    @classmethod
    def from_dicts(cls, dicts: List[Dict[str, Any]]) -> List['Fill']:
        return [cls(**d) for d in dicts]


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


@attrs
class OrderRecord:
    symbol: TradingPair = attrib(validator=instance_of(TradingPair), converter=TradingPair.from_str)
    orderId: str = attrib(converter=str)
    orderListId: str = attrib(converter=str)   # Unless OCO, value will be -1
    clientOrderId: str = attrib(converter=str)
    transactTime: int = attrib(converter=int)  # Timestamp in ms
    price: float = attrib(converter=float)
    origQty: float = attrib(converter=float)  # Quantity set in the order
    executedQty: float = attrib(converter=float)
    cummulativeQuoteQty: float = attrib(converter=float)
    status: str = attrib(converter=str)
    timeInForce: TimeInForce = attrib(converter=TimeInForce.__getitem__)
    type: OrderType = attrib(converter=OrderType.__getitem__)
    side: Side = attrib(converter=Side.__getitem__)
    fills: List[Fill] = attrib(converter=Fill.from_dicts)


