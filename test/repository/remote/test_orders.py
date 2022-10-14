from typing import List

import pytest

from conf.consts import TimeInForce, OrderType, Side, CryptoAsset
from repository.db import Fill, Order


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
def uns_fills(api_response) -> List[dict]:
    return api_response["fills"]


@pytest.fixture
def uns_fill(uns_fills) -> dict:
    return uns_fills[0]


@pytest.fixture
def struct_fill(uns_fill) -> Fill:
    return Fill(price="271.70000000", qty="3.50000000", commission="0.00000000", commissionAsset="BUSD", tradeId=11243)


@pytest.fixture
def struct_fills(uns_fills) -> List[Fill]:
    return [
        Fill(
            price=f["price"],
            qty=f["qty"],
            commission=f["commission"],
            commissionAsset=f["commissionAsset"],
            tradeId=f["tradeId"],
        )
        for f in uns_fills
    ]


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
        status="FILLED",
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


def test_structure_fill(uns_fill, struct_fill):
    assert Fill.structure(uns_fill) == struct_fill


def test_structure_fills(uns_fills, struct_fills):
    assert Fill.structure(uns_fills) == struct_fills


def test_structure_order(api_response, struct_order):
    assert Order.structure(api_response) == struct_order
