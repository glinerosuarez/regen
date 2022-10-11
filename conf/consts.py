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


class Action(enum.Enum):
    Sell = 0
    Buy = 1


class Position(enum.Enum):
    """
    When speaking of stocks and options, analysts and market makers often refer to an investor having long positions or
    short positions. While long and short in financial matters can refer to several things, in this context, rather than
    a reference to length, long positions and short positions are a reference to what an investor owns and stocks an
    investor needs to own.
    """

    # If the investor has short positions, it means that the investor owes those stocks to someone, but does not
    # actually own them yet. an investor who has sold 100 shares of TSLA without yet owning those shares is said to be
    # short 100 shares. The short investor owes 100 shares at settlement and must fulfill the obligation by purchasing
    # the shares in the market to deliver.
    Short = 0
    # If an investor has long positions, it means that the investor has bought and owns those shares of stocks.
    # For instance, an investor who owns 100 shares of Tesla (TSLA) stock in their portfolio is said to be long 100
    # shares. This investor has paid in full the cost of owning the shares.
    Long = 1

    def opposite(self):
        return Position.Short if self == Position.Long else Position.Long


class Algorithm(enum.Enum):
    PPO = "PPO"
