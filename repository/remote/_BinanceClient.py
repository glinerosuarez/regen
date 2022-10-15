import random
from collections import namedtuple
from logging import Logger
from typing import Optional, List, Union

import pendulum
import requests
from attr import define, field
from attrs import validators
from binance.spot import Spot
from binance.error import ClientError
from cached_property import cached_property

from conf.consts import Side, OrderType, TimeInForce, OrderStatus
from repository import Interval
from repository._consts import AvgPrice
from functions.utils import remove_none_args
from repository._dataclass import TradingPair
from repository.db import AccountInfo, Order, Kline, DataBaseManager

OrderData = namedtuple("OrderData", ["base_qty", "quote_qty", "price"])


@define(slots=False)
class BinanceClient:
    """Binance api client."""

    base_urls: List[str] = field(validator=validators.instance_of(list))
    client_key: str
    client_secret: str
    db_manager: DataBaseManager
    logger: Logger

    @cached_property
    def _spot_client(self) -> Spot:
        """Init a new spot client."""
        base_url = random.choice(self.base_urls)
        client = Spot(base_url=base_url, key=self.client_key, secret=self.client_secret)
        self.logger.debug(f"Getting new spot client {client} with base_url: {base_url}")
        return client

    def _invalidate_spot_client_cache(self) -> None:
        del self.__dict__["_spot_client"]

    def get_account_info(self) -> AccountInfo:
        """
        Get account information
        """
        return AccountInfo(**self._spot_client.account())

    def get_price(self, pair: TradingPair) -> float:
        """
        Get the current price of an asset.
        :param pair: trading pair.
        :return: Latest price for a symbol
        """
        return float(self._spot_client.ticker_price(str(pair))["price"])

    def get_current_avg_price(self, pair: TradingPair) -> AvgPrice:
        """
        Get the average price of a base in the quote units within a predefined length of time.
        :param pair: trading pair.
        :return: AvgPrice record
        """
        return AvgPrice(**self._spot_client.avg_price(str(pair)))

    def get_klines_data(
        self,
        pair: TradingPair,
        interval: Interval,
        start_time: Union[Optional[pendulum.DateTime], int] = None,
        end_time: Union[Optional[pendulum.DateTime], int] = None,
        limit: Optional[int] = None,
    ) -> List[Kline]:
        """
        Kline/Candlestick Data

        :param pair: the trading pair.
        :param interval: the interval of kline, e.g 1m, 5m, 1h, 1d, etc.
        :param start_time: datetime to get aggregate trades from INCLUSIVE.
        :param end_time: datetime to get aggregate trades until INCLUSIVE.
        :param limit: limit the results. Default 500; max 500.
        """
        # Convert datetimes to ts
        if isinstance(start_time, pendulum.DateTime):
            start_time = int(start_time.timestamp() * 1000)
        if isinstance(end_time, pendulum.DateTime):
            end_time = int(end_time.timestamp() * 1000)

        # Arguments to kwargs
        args = remove_none_args({"startTime": start_time, "endTime": end_time, "limit": limit})
        try:
            response = self._spot_client.klines(symbol=str(pair), interval=interval.value, **args)
        except requests.exceptions.ConnectionError as connection_err:
            self.logger.error(f"Remote disconnected connection_err: {connection_err}")
            self._invalidate_spot_client_cache()
            return self.get_klines_data(pair, interval, start_time, end_time, limit)  # Retry request.

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
        env_state_id: int,
        pair: TradingPair,
        side: Side,
        type: OrderType,
        time_in_force: Optional[TimeInForce] = None,
        quantity: Optional[float] = None,
        quoteOrderQty: Optional[float] = None,
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
        :param quantity: the quantity of the base asset that you want to buy or sell.
        :param quoteOrderQty:
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
                "timeInForce": None if time_in_force is None else time_in_force.value,
                "quantity": quantity,
                "quoteOrderQty": quoteOrderQty,
                "price": price,
                "newClientOrderId": new_client_order_id,
            }
        )
        try:
            if is_test:
                self.logger.debug(f"Executing test order with args: {args}.")
                self._spot_client.new_order_test(**args)
                return None
            else:
                self.logger.debug(f"Executing order with args: {args}.")
                result = Order(**{**{"env_state_id": env_state_id}, **self._spot_client.new_order(**args)})
                self.logger.debug(f"Inserting order record {result} to db.")
                self.db_manager.insert(result)

                if result.status == OrderStatus.FILLED:
                    return result
                else:
                    # TODO: handle scenario when order is EXPIRED (no liquidity)
                    self.logger.error(f"Order request with args: {args} could not be filled, result: {result}.")
                    return None  # TODO: handle this scenario
        except ClientError as e:
            self.logger.error(e)
            return None  # TODO: handle this scenario

    def buy_at_market(
        self, env_state_id: int, pair: TradingPair, quantity: Optional[float] = None
    ) -> Optional[OrderData]:
        """
        Buy a base at market price. By default, asks the engine to complete the order immediately or kill it if it's not
        possible.
        :param env_state_id:
        :param pair: Base quote pair.
        :param quantity: Quantity (in quote units) to buy the base.
        :return: Order data.
        """
        o = self.place_order(
            env_state_id=env_state_id,
            pair=pair,
            side=Side.BUY,
            type=OrderType.MARKET,
            quoteOrderQty=quantity,
            is_test=False,
        )
        if o is None:
            return None
        else:
            self.logger.debug(f"Buy order filled: {o}.")
            return OrderData(o.executedQty, quantity - o.cummulativeQuoteQty, o.cummulativeQuoteQty / o.executedQty)

    def sell_at_market(
        self, env_state_id: int, pair: TradingPair, quantity: Optional[float] = None
    ) -> Optional[OrderData]:
        """
        Sell a base at market price. By default, asks the engine to complete the order immediately or kill it if it's
        not possible.
        :param env_state_id:
        :param pair: Base quote pair.
        :param quantity: Quantity (in base units) to sell the base.
        :return: Remaining balance (in base units), total received quantity (in quote units) and avg price we sold at
                 (in quote units).
        """
        o = self.place_order(
            env_state_id=env_state_id,
            pair=pair,
            side=Side.SELL,
            type=OrderType.MARKET,
            quantity=quantity,
            is_test=False,
        )

        if o is None:
            return None
        else:
            self.logger.debug(f"Sell order filled: {o}.")
            return OrderData(quantity - o.executedQty, o.cummulativeQuoteQty, o.cummulativeQuoteQty / o.executedQty)
