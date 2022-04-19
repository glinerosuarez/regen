from consts import CryptoAsset
from repository._dataclass import TradingPair


def test_tradingpair_from_str():
    # Positive scenario
    pair = TradingPair.from_str(CryptoAsset.BNB.value + CryptoAsset.BUSD.value)
    assert pair is not None
    assert pair.base == CryptoAsset.BNB and pair.quote == CryptoAsset.BUSD

    # Positive scenario with polluted str
    pair = TradingPair.from_str("boff" + CryptoAsset.BTC.value + "azou" + CryptoAsset.BUSD.value + "tra")
    assert pair is not None
    assert pair.base == CryptoAsset.BTC and pair.quote == CryptoAsset.BUSD

    # Negative scenario
    pair = TradingPair.from_str("boff" + "izsh" + "boff" + "tra")
    assert pair is None

    # Negative scenario only a single crypto asset found
    pair = TradingPair.from_str("boff" + CryptoAsset.ETH.value + "boff" + "tra")
    assert pair is None
