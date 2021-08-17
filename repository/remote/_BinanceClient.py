from datetime import datetime

from config import settings
from typing import Dict, Any, Optional, List, Union
from binance.spot import Spot

from consts import CryptoAsset, TradingPair, KlineRecord
from repository import Interval


class BinanceClient:
    """
    Binance api client.
    """

    client = Spot(base_url=settings.bnb_base_url, key=settings.bnb_client_key, secret=settings.bnb_client_secret)

    def get_account_info(self) -> Dict[str, Any]:
        """
         Get account information
        """
        return self.client.account()

    def get_klines_data(
            self,
            pair: TradingPair,
            interval: Interval,
            start_time: Optional[int] = None,
            end_time: Optional[int] = None,
            limit: Optional[int] = None,
    ) -> List[KlineRecord]:
        """
        Kline/Candlestick Data

        :param pair: the trading pair.
        :param interval: the interval of kline, e.g 1m, 5m, 1h, 1d, etc.
        :param start_time: Timestamp in ms to get aggregate trades from INCLUSIVE.
        :param end_time: Timestamp in ms to get aggregate trades until INCLUSIVE.
        :param limit: limit the results. Default 500; max 1000.
        """
        # Arguments to kwargs
        args = {
            k: v
            for k, v in {"start_time": start_time, "end_time": end_time, "limit": limit}.items()
            if v is not None
        }
        print(args)
        response = self.client.klines(symbol=pair.to_symbol(), interval=interval.value, start_time=start_time)

        return [
            KlineRecord(
                pair=pair,
                open_time=r[0],
                open_value=r[1],
                high=r[2],
                low=r[3],
                close_value=r[4],
                volume=r[5],
                close_time=r[6],
                quote_asset_vol=r[7],
                trades=r[8],
                taker_buy_base_vol=r[9],
                taker_buy_quote_vol=r[10],
            )
            for r in response
        ]
