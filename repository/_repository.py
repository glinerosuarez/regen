from repository.remote import BinanceClient


class Repository:

    bnb_client = BinanceClient()

    @classmethod
    def get_account_info(cls):
        return cls.bnb_client.get_account_info()

    @staticmethod
    def get_klines_data():
        pass
