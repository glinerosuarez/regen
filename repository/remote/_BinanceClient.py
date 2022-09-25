import random
from logging import Logger
from typing import Optional, List

import pendulum
import requests
from binance.spot import Spot
from binance.error import ClientError

import conf
from conf.consts import Side, OrderType, TimeInForce
from log import LoggerFactory
from repository import Interval
from repository._consts import AvgPrice
from functions.utils import remove_none_args
from repository._dataclass import TradingPair
from repository.db import AccountInfo, Order, Kline


class BinanceClient:
    """
    Binance api client.
    """

    def get_client(self, use_default_url: bool = True) -> Spot:
        """
        Init a new spot client.
        :param use_default_url: If True, then use the first url provided in settings.bnb_client_key, else choose a
            random one.
        """
        if (self._client is None) or (not use_default_url):
            base_url = (
                conf.settings.bnb_base_url[0] if use_default_url is True else random.choice(conf.settings.bnb_base_url)
            )
            self._client = Spot(
                base_url=base_url, key=conf.settings.bnb_client_key, secret=conf.settings.bnb_client_secret
            )
            return self._client
        else:
            return self._client

    def __init__(self):
        self._client = None
        self.logger: Logger = LoggerFactory.get_console_logger(__name__)

    def get_account_info(self) -> AccountInfo:
        """
        Get account information
        """
        return AccountInfo(**self.get_client().account())

    def get_price(self, pair: TradingPair) -> float:
        """
        Get the current price of an asset.
        :param pair: trading pair.
        :return: Latest price for a symbol
        """
        return float(self.get_client().ticker_price(str(pair))["price"])

    def get_current_avg_price(self, pair: TradingPair) -> AvgPrice:
        """
        Get the average price of a base in the quote units within a predefined length of time.
        :param pair: trading pair.
        :return: AvgPrice record
        """
        return AvgPrice(**self.get_client().avg_price(str(pair)))

    def get_klines_data(
        self,
        pair: TradingPair,
        interval: Interval,
        start_time: Optional[pendulum.DateTime] = None,
        end_time: Optional[pendulum.DateTime] = None,
        limit: Optional[int] = None,
    ) -> List[Kline]:
        """
        Kline/Candlestick Data

        :param pair: the trading pair.
        :param interval: the interval of kline, e.g 1m, 5m, 1h, 1d, etc.
        :param start_time: datetime to get aggregate trades from INCLUSIVE.
        :param end_time: datetime to get aggregate trades until INCLUSIVE.
        :param limit: limit the results. Default 500; max 1000.
        """
        # Convert datetimes to ts
        start_time_ts = None if start_time is None else int(start_time.timestamp() * 1000)
        end_time_ts = None if end_time is None else int(end_time.timestamp() * 1000)

        # Arguments to kwargs
        args = remove_none_args({"startTime": start_time_ts, "endTime": end_time_ts, "limit": limit})
        try:
            response = self.get_client().klines(symbol=str(pair), interval=interval.value, **args)
        except requests.exceptions.ConnectionError as connection_err:
            self.logger.error(f"Remote disconnected connection_err: {connection_err}")
            return self.get_client(False).get_klines_data(pair, interval, start_time, end_time, limit)  # Retry request.

        return [
            Kline(
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

    def place_order(
        self,
        pair: TradingPair,
        side: Side,
        type: OrderType,
        time_in_force: TimeInForce = TimeInForce.GTC,
        quantity: Optional[float] = None,
        price: Optional[float] = None,
        new_client_order_id: Optional[str] = None,
        is_test: bool = True,
    ) -> Optional[Order]:
        """
        Set a test order. Can come in useful for testing orders before actually submitting them.
        :param pair: pair to trade.
        :param side: whether you want to BUY or SELL.
        :param type: the type of order you want to submit.
        :param time_in_force: this parameter expresses how you want the order to execute.
        :param quantity: the quantity of the asset that you want to buy or sell.
        :param price: the price at which you want to sell.
        :param new_client_order_id: an identifier for the order.
        :return: true if the order can be created.
        :param is_test: whether this a test order or not.
        """

        # Arguments to kwargs
        args = remove_none_args(
            {
                "symbol": str(pair),
                "side": side.value,
                "type": type.value,
                "timeInForce": time_in_force.value,
                "quantity": quantity,
                "price": price,
                "newClientOrderId": new_client_order_id,
            }
        )
        try:
            if is_test:
                self.get_client().new_order_test(**args)
                return None
            else:
                return Order(**self.get_client().new_order(**args))
        except ClientError as e:
            LoggerFactory.get_console_logger(__name__).error(e)
