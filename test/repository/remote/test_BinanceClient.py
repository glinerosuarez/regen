from repository.remote import BinanceClient


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

    assert BinanceClient().get_account_info() == expected_account_info
