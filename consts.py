import attr
import enum
import sqlite3
from attr import attrs
from copy import deepcopy
from attr.validators import instance_of
from typing import Optional, List, Dict, Any, NamedTuple, Type, Tuple, Union


@attrs
class DataClass:

    class Items(NamedTuple):
        attrs: Tuple[str]
        values: Tuple[Any]

    class Types(NamedTuple):
        attrs: Tuple[str]
        types: Tuple[Type[Any]]

    @classmethod
    def from_dict(cls, d) -> 'DataClass':
        return cls(**d)

    @classmethod
    def from_dicts(cls, dicts: List[Dict[str, Any]]) -> List['DataClass']:
        """Create a list of instances of this class from a list of dicts."""
        return [cls.from_dict(d) for d in dicts]

    @classmethod
    def from_items(cls, items: 'DataClass.Items') -> List['DataClass']:
        return [cls(**dict(zip(i.attrs, i.values))) for i in items]

    @classmethod
    def from_list(cls, values: Union[List[dict], List['DataClass']]) -> List['DataClass']:
        if isinstance(values[0], dict):
            return cls.from_dicts(values)
        elif isinstance(values[0], cls):
            return values
        else:
            TypeError(f"type {type(values)} is not supported.")

    @classmethod
    def get_types(cls) -> Types:
        """Get the types of each attribute."""
        return DataClass.Types(*zip(*[(a.name, a.type) for a in attr.fields(cls)]))

    def to_dict(self) -> Dict[str, Any]:
        """Attributes and their corresponding values as a dict."""
        return attr.asdict(self)

    def get_items(self) -> Items:
        """Return a tuple that contains the names of the attributes and their corresponding values."""
        return DataClass.Items(*zip(*self.to_dict().items()))

    def copy(self, _with: dict) -> 'DataClass':
        attribs = deepcopy(self.to_dict())
        for k, v in _with.items():
            attribs[k] = v
        return self.__class__(**attribs)


class SQLEnum(enum.Enum):

    def __str__(self):
        return self.value

    def __conform__(self, protocol):
        """Transforms an `Enum` object into a `str` for storing in a sql db."""
        if protocol is sqlite3.PrepareProtocol:
            return str(self)

    @classmethod
    def converter(cls, src: Union[str, 'SQLEnum']) -> 'SQLEnum':
        if isinstance(src, str):
            return cls[src]
        elif isinstance(src, cls):
            return src
        else:
            raise TypeError(f"type {type(src)} is not supported.")

    @classmethod
    def from_list(cls, sql_enums: List[Union[str, 'SQLEnum']]) -> List['SQLEnum']:
        return [cls.converter(e) for e in sql_enums]


class EnvConsts:

    MAX_ACCOUNT_BALANCE = 1000.0

    INITIAL_ACCOUNT_BALANCE = 1.0

    MAX_SHARE_PRICE = 300.0

    MAX_NUM_SHARES = 10.0

    MAX_STEPS = 20000

    LOOKBACK_WINDOW_SIZE = 40


class Side(SQLEnum):
    """Whether you want to BUY or SELL a base."""
    BUY: str = 'BUY'
    SELL: str = 'SELL'


class OrderType(SQLEnum):
    """The type of order you want to submit."""
    LIMIT: str = 'LIMIT'
    MARKET: str = 'MARKET'
    STOP_LOSS: str = 'STOP_LOSS'
    STOP_LOSS_LIMIT: str = 'STOP_LOSS_LIMIT'
    TAKE_PROFIT: str = 'TAKE_PROFIT'
    TAKE_PROFIT_LIMIT: str = 'TAKE_PROFIT_LIMIT'
    LIMIT_MAKER: str = 'LIMIT_MAKER'


class TimeInForce(SQLEnum):
    """Expresses how you want the order to execute."""
    # (good till canceled) – perhaps the most popular setup, GTC will ensure that your order is valid until it’s filled,
    # or until you cancel it.
    GTC: str = 'GTC'
    # (fill or kill) – FOK instructs the exchange to execute an order all at once. If the exchange can’t do so, the
    # order is immediately canceled.
    FOK: str = 'FOK'
    # (immediate or cancel) – either all or part of the order must be executed immediately, or it’s canceled. Unlike
    # FOK, the orders are not canceled if they can be partially filled.
    IOC: str = 'IOC'


class CryptoAsset(SQLEnum):

    BNB: str = 'BNB'
    ETH: str = 'ETH'
    BTC: str = 'BTC'
    LTC: str = 'LTC'
    TRX: str = 'TRX'
    XRP: str = 'XRP'
    USDT: str = 'USDT'
    BUSD: str = 'BUSD'


@attrs
class TradingPair(DataClass):
    base: CryptoAsset = attr.attrib(validator=instance_of(CryptoAsset), converter=CryptoAsset.converter)
    quote: CryptoAsset = attr.attrib(validator=instance_of(CryptoAsset), converter=CryptoAsset.converter)

    @staticmethod
    def from_str_or_dict(source: Union[str, dict]) -> 'TradingPair':
        if isinstance(source, str):
            return TradingPair.from_str(source)
        elif isinstance(source, dict):
            return TradingPair.from_dict(source)
        else:
            raise TypeError(f"type {type(source)} is not supported.")

    @classmethod
    def from_str(cls, string: str) -> Optional['TradingPair']:
        # First crypto asset str found
        f1 = None
        # Second crypto asset str found
        f2 = None
        # Index of the f1
        first = None
        # Index of the f2
        second = None

        for ca in CryptoAsset:
            # Check if a crypto asset str is found
            index = string.find(ca.value)
            if index != -1:
                # If the first crypto asset str has not been found yet, assign vars
                if first is None:
                    f1 = ca
                    first = index
                # Otherwise assign second finding vars
                elif second is None:
                    f2 = ca
                    second = index
                    # We have all what we need, stop searching
                    break
        else:
            # Return None since we have not found a valid crypto pair
            return None
        # Instantiate TradingPair, first occurrence as base and the other as quote
        return cls(base=f1, quote=f2) if first < second else cls(base=f2, quote=f1)

    def to_symbol(self):
        return self.base.value + self.quote.value
