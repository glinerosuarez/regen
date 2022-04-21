from enum import Enum
from typing import TypeVar


E = TypeVar("E")


class Action(Enum):
    Sell = 0
    Buy = 1


class Position(Enum):
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
