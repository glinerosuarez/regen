import enum


class EnvConsts:

    MAX_ACCOUNT_BALANCE = 1000.0

    INITIAL_ACCOUNT_BALANCE = 1.0

    MAX_SHARE_PRICE = 300.0

    MAX_NUM_SHARES = 10.0

    MAX_STEPS = 20000

    LOOKBACK_WINDOW_SIZE = 40


class Side(enum.Enum):
    """Whether you want to BUY or SELL a base."""

    BUY: str = "BUY"
    SELL: str = "SELL"


class OrderType(enum.Enum):
    """The type of order you want to submit."""

    LIMIT: str = "LIMIT"
    MARKET: str = "MARKET"
    STOP_LOSS: str = "STOP_LOSS"
    STOP_LOSS_LIMIT: str = "STOP_LOSS_LIMIT"
    TAKE_PROFIT: str = "TAKE_PROFIT"
    TAKE_PROFIT_LIMIT: str = "TAKE_PROFIT_LIMIT"
    LIMIT_MAKER: str = "LIMIT_MAKER"


class TimeInForce(enum.Enum):
    """Expresses how you want the order to execute."""

    # (good till canceled) – perhaps the most popular setup, GTC will ensure that your order is valid until it’s filled,
    # or until you cancel it.
    GTC: str = "GTC"
    # (fill or kill) – FOK instructs the exchange to execute an order all at once. If the exchange can’t do so, the
    # order is immediately canceled.
    FOK: str = "FOK"
    # (immediate or cancel) – either all or part of the order must be executed immediately, or it’s canceled. Unlike
    # FOK, the orders are not canceled if they can be partially filled.
    IOC: str = "IOC"


class CryptoAsset(enum.Enum):
    """Crypto asset symbols."""

    BNB: str = "BNB"
    ETH: str = "ETH"
    BTC: str = "BTC"
    LTC: str = "LTC"
    TRX: str = "TRX"
    XRP: str = "XRP"
    USDT: str = "USDT"
    BUSD: str = "BUSD"
