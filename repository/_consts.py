from enum import Enum
from attr import attrs, attrib
from attr.validators import instance_of
from consts import TradingPair, TimeInForce, OrderType, Side, CryptoAsset, DataClass, SQLEnum


class AccountType(SQLEnum):
    SPOT = 'SPOT'


class AccountPermission(SQLEnum):
    SPOT = 'SPOT'


class Interval(Enum):
    M_1 = '1m'
    M_5 = '5m'
    H_1 = '1h'
    D_1 = '1d'


@attrs
class Fill(DataClass):
    price: float = attrib(converter=float)
    qty: float = attrib(converter=float)
    commission: float = attrib(converter=float)
    commissionAsset: CryptoAsset = attrib(converter=CryptoAsset.converter)


@attrs
class Balance(DataClass):
    asset: CryptoAsset = attrib(converter=CryptoAsset.converter)
    free: float = attrib(converter=float)
    locked: float = attrib(converter=float)


@attrs
class AccountInfo(DataClass):
    # When you add an order that doesn't match existing offers, you add liquidity to the market and are charged a maker
    # fee
    makerCommission: float = attrib(converter=float)
    # When you create an order that is immediately matched with already existing orders, you're a taker because you take
    # liquidity from the market
    takerCommission: float = attrib(converter=float)
    buyerCommission: float = attrib(converter=float)
    sellerCommission: float = attrib(converter=float)
    canTrade: bool = attrib(converter=bool)
    canWithdraw: bool = attrib(converter=bool)
    canDeposit: bool = attrib(converter=bool)
    updateTime: int = attrib(converter=int)
    accountType: AccountType = attrib(converter=AccountType.converter)
    balances: list = attrib(converter=Balance.from_list)
    permissions: list = attrib(converter=AccountPermission.from_list)


@attrs
class AvgPrice:
    mins: int = attrib(converter=int)  # Minutes to compute average
    price: float = attrib(converter=float)


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
class OrderRecord(DataClass):
    """Data of a placed order."""
    symbol: TradingPair = attrib(validator=instance_of(TradingPair), converter=TradingPair.from_str_or_dict)
    orderId: str = attrib(converter=str)
    orderListId: str = attrib(converter=str)  # Unless OCO, value will be -1
    clientOrderId: str = attrib(converter=str)
    transactTime: int = attrib(converter=int)  # Timestamp in ms
    price: float = attrib(converter=float)
    origQty: float = attrib(converter=float)  # Quantity set in the order
    executedQty: float = attrib(converter=float)
    cummulativeQuoteQty: float = attrib(converter=float)
    status: str = attrib(converter=str)
    timeInForce: TimeInForce = attrib(converter=TimeInForce.converter)
    type: OrderType = attrib(converter=OrderType.converter)
    side: Side = attrib(converter=Side.converter)
    fills: list = attrib(converter=Fill.from_dicts)
