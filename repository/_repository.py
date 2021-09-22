from repository.remote import BinanceClient


class Repository:

    _bnb_client: BinanceClient = BinanceClient()

    @staticmethod
    def get_account_info():
        """
         Get account information
        """
        return Repository._bnb_client.get_account_info()

    @staticmethod
    def get_klines_data():
        return Repository._bnb_client.get_klines_data()
