from typing import List

import pytest

from conf import OrderType
from conf.consts import OrderStatus, TimeInForce, Side, CryptoAsset
from repository.db import Order, Fill


@pytest.fixture
def struct_order(api_response, trading_pair) -> Order:
    return Order(
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
        fills=[
            Fill(price=271.7, qty=3.5, commission=0.0, commissionAsset=CryptoAsset.BUSD, tradeId=11243),
            Fill(price=271.5, qty=3.14, commission=0.0, commissionAsset=CryptoAsset.BUSD, tradeId=11244),
            Fill(price=271.2, qty=2.59, commission=0.0, commissionAsset=CryptoAsset.BUSD, tradeId=11245),
            Fill(price=271.1, qty=0.77, commission=0.0, commissionAsset=CryptoAsset.BUSD, tradeId=11246),
        ],
    )


@pytest.fixture
def orders(struct_order) -> List[Order]:
    data_2 = struct_order.copy(with_={"symbol": "ETHBUSD"})
    data_3 = struct_order.copy(with_={"symbol": "BTCUSDT", "orderId": "67890"})
    data_4 = struct_order.copy(with_={"symbol": "BTCUSDT", "orderId": "11121", "clientOrderId": "anyid"})

    return [struct_order, data_2, data_3, data_4]
