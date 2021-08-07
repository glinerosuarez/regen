from attr import attrs
from binance.spot import Spot


class URL:
    """Base endpoints to Binance apis."""
    TESTNET = 'https://testnet.binance.vision'


@attrs(auto_attribs=True)
class BinanceClient:
    # The base endpoint this client will send requests to.
    base_url: str

    client = Spot(base_url=base_url, key=)