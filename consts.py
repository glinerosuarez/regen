import enum
from dataclasses import dataclass
from typing import Optional


class EnvConsts:

    MAX_ACCOUNT_BALANCE = 1000.0

    INITIAL_ACCOUNT_BALANCE = 1.0

    MAX_SHARE_PRICE = 300.0

    MAX_NUM_SHARES = 10.0

    MAX_STEPS = 20000

    LOOKBACK_WINDOW_SIZE = 40


class Side(enum.Enum):
    """Whether you want to BUY or SELL a base."""
    BUY: str = 'BUY'
    SELL: str = 'SELL'


class OrderType(enum.Enum):
    """The type of order you want to submit."""
    LIMIT: str = 'LIMIT'
    MARKET: str = 'MARKET'
    STOP_LOSS: str = 'STOP_LOSS'
    STOP_LOSS_LIMIT: str = 'STOP_LOSS_LIMIT'
    TAKE_PROFIT: str = 'TAKE_PROFIT'
    TAKE_PROFIT_LIMIT: str = 'TAKE_PROFIT_LIMIT'
    LIMIT_MAKER: str = 'LIMIT_MAKER'


class TimeInForce(enum.Enum):
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
