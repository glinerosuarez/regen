import pendulum

from conf.consts import CryptoAsset
from repository._dataclass import TradingPair
from repository._consts import AccountType, AccountPermission, Interval


def test_get_account_info(api_client):
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
    account_data = api_client.get_account_info()
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


def test_get_klines_data(api_client):
    now = pendulum.now()
    close_time = now.subtract(minutes=1).end_of("minute")
    open_time = now.subtract(minutes=6).start_of("minute")
    response = api_client.get_klines_data(
        TradingPair(CryptoAsset.BNB, CryptoAsset.USDT), Interval.M_1, open_time, close_time
    )
    assert len(response) == 6
    assert response[0].open_time == open_time.timestamp() * 1_000
    assert response[-1].close_time == int(close_time.timestamp() * 1_000)


def test_get_price(api_client):
    price = api_client.get_price(TradingPair(CryptoAsset.BNB, CryptoAsset.BUSD))
    assert isinstance(price, float)
