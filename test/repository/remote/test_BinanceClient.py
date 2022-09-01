from datetime import datetime

from consts import Side, OrderType
from repository.remote import BinanceClient
from consts import CryptoAsset, TimeInForce
from functions.utils import datetime_to_ts_ms
from repository._dataclass import TradingPair
from repository._consts import AccountType, AccountPermission, Interval

client = BinanceClient()


def test_get_account_info():
    maker_commission = 0
    taker_commission = 0
    buyer_commission = 0
    seller_commission = 0
    can_trade = True
    can_withdraw = False
    can_deposit = False
    account_type = AccountType.SPOT
    balance_assets = [
        CryptoAsset.BNB,
        CryptoAsset.BTC,
        CryptoAsset.BUSD,
        CryptoAsset.ETH,
        CryptoAsset.LTC,
        CryptoAsset.TRX,
        CryptoAsset.USDT,
        CryptoAsset.XRP,
    ]
    permissions = [AccountPermission.SPOT]

    # Test fixed values
    account_data = client.get_account_info()
    assert account_data.makerCommission == maker_commission
    assert account_data.takerCommission == taker_commission
    assert account_data.buyerCommission == buyer_commission
    assert account_data.sellerCommission == seller_commission
    assert account_data.canTrade == can_trade
    assert account_data.canWithdraw == can_withdraw
    assert account_data.canDeposit == can_deposit
    assert account_data.accountType == account_type
    assert [b.asset for b in account_data.balances] == balance_assets
    assert account_data.permissions == permissions


def test_get_klines_data():
    close_time = datetime(year=2022, month=8, day=13, hour=13, minute=35)
    open_time = datetime(year=2022, month=8, day=13, hour=13, minute=30)
    response = client.get_klines_data(
        TradingPair(CryptoAsset.BNB, CryptoAsset.USDT), Interval.M_1, open_time, close_time
    )
    assert len(response) == 6
    assert response[0].open_time == open_time.timestamp() * 1_000
    assert response[-1].open_time == close_time.timestamp() * 1_000


def test_place_test_order():
    pair = TradingPair(CryptoAsset.BNB, CryptoAsset.USDT)
    price = int(client.get_current_avg_price(pair).price * 1.1)
    print("price", price)
    assert (
        client.place_order(
            pair=pair,
            side=Side.SELL,
            type=OrderType.LIMIT,
            quantity=0.1,
            price=price,
        )
        is None
    )


def test_place_order():
    # Test fixed values
    tp = TradingPair(CryptoAsset.BNB, CryptoAsset.USDT)
    clientid = str(int(datetime.now().timestamp()))
    tt = datetime_to_ts_ms(datetime.now())
    price = 1000.0
    qtty = 0.1
    type = OrderType.LIMIT
    side = Side.SELL
    order_data = client.place_order(
        pair=tp, side=side, type=type, quantity=qtty, price=price, is_test=False, new_client_order_id=clientid
    )

    assert order_data.symbol == tp
    assert order_data.clientOrderId == clientid
    assert order_data.transactTime > tt
    assert order_data.price == price
    assert order_data.origQty == qtty
    assert order_data.timeInForce == TimeInForce.GTC
    assert order_data.type == type
    assert order_data.side == side


def test_get_price():
    price = client.get_price(TradingPair(CryptoAsset.BNB, CryptoAsset.BUSD))
    assert isinstance(price, float)
