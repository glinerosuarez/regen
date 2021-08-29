from repository.remote import BinanceClient


class Repository:

    bnb_client = BinanceClient()

    @classmethod
    def get_account_info(cls):
        """
         Get account information
        """
        return cls.bnb_client.get_account_info()

    @classmethod
    def get_klines_data(cls):
        return cls.bnb_client.get_klines_data()
