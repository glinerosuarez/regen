from typing import List

import pytest

from conf import OrderType
from conf.consts import OrderStatus, TimeInForce, Side, CryptoAsset
from repository.db import Order, Fill


@pytest.fixture
def env_state_id() -> int:
    return 1


@pytest.fixture
def api_response() -> dict:
    return {
        "symbol": "BNBBUSD",
        "orderId": 271468,
        "orderListId": -1,
        "clientOrderId": "AS8MQlzMS8vEGwobLGWpN5",
        "transactTime": 1665544366616,
        "price": "0.00000000",
        "origQty": "10.00000000",
        "executedQty": "10.00000000",
        "cummulativeQuoteQty": "2714.61500000",
        "status": "FILLED",
        "timeInForce": "GTC",
        "type": "MARKET",
        "side": "SELL",
        "workingTime": 1507725176595,
        "selfTradePreventionMode": "NONE",
        "fills": [
            {
                "price": "271.70000000",
                "qty": "3.50000000",
                "commission": "0.00000000",
                "commissionAsset": "BUSD",
                "tradeId": 11243,
            },
            {
                "price": "271.50000000",
                "qty": "3.14000000",
                "commission": "0.00000000",
                "commissionAsset": "BUSD",
                "tradeId": 11244,
            },
            {
                "price": "271.20000000",
                "qty": "2.59000000",
                "commission": "0.00000000",
                "commissionAsset": "BUSD",
                "tradeId": 11245,
            },
            {
                "price": "271.10000000",
                "qty": "0.77000000",
                "commission": "0.00000000",
                "commissionAsset": "BUSD",
                "tradeId": 11246,
            },
        ],
    }


@pytest.fixture
def struct_order(api_response, trading_pair, env_state_id) -> Order:
    return Order(
        env_state_id=env_state_id,
        symbol=trading_pair,
        orderId="271468",
        orderListId="-1",
        clientOrderId="AS8MQlzMS8vEGwobLGWpN5",
        transactTime=1665544366616,
        price=0.00000000,
        origQty=10.00000000,
        executedQty=10.00000000,
        cummulativeQuoteQty=2714.61500000,
        status=OrderStatus.FILLED,
        timeInForce=TimeInForce.GTC,
        type=OrderType.MARKET,
        side=Side.SELL,
        workingTime=1507725176595,
        selfTradePreventionMode="NONE",
        fills=[
            Fill(price=271.7, qty=3.5, commission=0.0, commissionAsset=CryptoAsset.BUSD, tradeId=11243),
            Fill(price=271.5, qty=3.14, commission=0.0, commissionAsset=CryptoAsset.BUSD, tradeId=11244),
            Fill(price=271.2, qty=2.59, commission=0.0, commissionAsset=CryptoAsset.BUSD, tradeId=11245),
            Fill(price=271.1, qty=0.77, commission=0.0, commissionAsset=CryptoAsset.BUSD, tradeId=11246),
        ],
    )


@pytest.fixture
def orders(struct_order, env_state_id) -> List[Order]:
    data_2 = struct_order.copy(with_={"symbol": "ETHBUSD", "env_state_id": env_state_id + 1})
    data_3 = struct_order.copy(with_={"symbol": "BTCUSDT", "orderId": "67890", "env_state_id": env_state_id + 2})
    data_4 = struct_order.copy(
        with_={"symbol": "BTCUSDT", "orderId": "11121", "clientOrderId": "anyid", "env_state_id": env_state_id + 3}
    )

    return [struct_order, data_2, data_3, data_4]
