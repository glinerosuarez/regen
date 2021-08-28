from datetime import datetime
from consts import CryptoAsset, TimeInForce
from utils import datetime_to_ts_ms
from repository.remote import BinanceClient
from consts import TradingPair, Side, OrderType

client = BinanceClient()


def test_get_account_info():
    expected_account_info = eval(
        """{
            'makerCommission': 0, 
            'takerCommission': 0, 
            'buyerCommission': 0, 
            'sellerCommission': 0, 
            'canTrade': True,
            'canWithdraw': False, 
            'canDeposit': False, 
            'updateTime': 1628352426818, 
            'accountType': 'SPOT', 
            'balances': [
                {'asset': 'BNB', 'free': '999.90000000', 'locked': '0.00000000'}, 
                {'asset': 'BTC', 'free': '1.00000000', 'locked': '0.00000000'}, 
                {'asset': 'BUSD', 'free': '10011.00000000', 'locked': '0.00000000'}, 
                {'asset': 'ETH', 'free': '100.00000000', 'locked': '0.00000000'}, 
                {'asset': 'LTC', 'free': '500.00000000', 'locked': '0.00000000'}, 
                {'asset': 'TRX', 'free': '500000.00000000', 'locked': '0.00000000'}, 
                {'asset': 'USDT', 'free': '10000.00000000', 'locked': '0.00000000'}, 
                {'asset': 'XRP', 'free': '50000.00000000', 'locked': '0.00000000'}
            ],
            'permissions': ['SPOT']
        }""")

    assert client.get_account_info() == expected_account_info


def test_get_klines_data():
    # TODO: test this on the real net because test net seems inconsistent.
    pass


def test_place_test_order():
    assert client.place_order(
        pair=TradingPair(CryptoAsset.BNB, CryptoAsset.USDT),
        side=Side.SELL,
        type=OrderType.LIMIT,
        quantity=0.1,
        price=9000,
    ) is False


def test_place_order():

    # Test fixed values
    tp = TradingPair(CryptoAsset.BNB, CryptoAsset.USDT)
    clientid = "azouta"
    tt = datetime_to_ts_ms(datetime.now())
    price = 1000.0
    qtty = 0.1
    type = OrderType.LIMIT
    side = Side.SELL
    order_data = client.place_order(
        pair=tp,
        side=side,
        type=type,
        quantity=qtty,
        price=price,
        is_test=False,
        new_client_order_id=clientid
    )

    assert order_data.symbol == tp
    assert order_data.clientOrderId == clientid
    assert order_data.transactTime > tt
    assert order_data.price == price
    assert order_data.origQty == qtty
    assert order_data.timeInForce == TimeInForce.GTC
    assert order_data.type == type
    assert order_data.side == side
