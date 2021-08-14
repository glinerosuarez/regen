from config import settings
from typing import Dict, Any
from binance.spot import Spot


class BinanceClient:

    client = Spot(base_url=settings.bnb_base_url, key=settings.bnb_client_key, secret=settings.bnb_client_secret)

    def get_account_info(self) -> Dict[str, Any]:
        """
         Get account information
        """
        return self.client.account()
