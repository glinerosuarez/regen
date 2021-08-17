from datetime import datetime

from consts import TradingPair
from consts import CryptoAsset
from repository import Interval
from repository.remote import BinanceClient

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
    print(
        len(
            client.get_klines_data(
                TradingPair(CryptoAsset.BNB, CryptoAsset.USDT),
                Interval.D_1,
                start_time=int(datetime.timestamp(datetime(year=2021, month=5, day=1)) * 1000),
                end_time=int(datetime.timestamp(datetime(year=2021, month=8, day=1)) * 1000),
                #limit=100,
            )
        )
    )
