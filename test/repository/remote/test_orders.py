from typing import List

import pendulum
import pytest

from conf.consts import OrderType, Side
from repository import TradingPair
from repository.db import Fill, Order


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
def liquid_symbol() -> TradingPair:
    return TradingPair.structure("BNBUSDT")


def test_place_test_order(api_client, liquid_symbol, env_state_id):
    assert (
        api_client.place_order(
            env_state_id=env_state_id,
            pair=liquid_symbol,
            side=Side.SELL,
            type=OrderType.MARKET,
            quantity=0.1,
        )
        is None
    )


def test_place_order(api_client, struct_order, liquid_symbol, env_state_id):
    # Test fixed values
    now = pendulum.now()
    order = api_client.place_order(
        env_state_id=env_state_id,
        pair=liquid_symbol,
        side=struct_order.side,
        type=struct_order.type,
        quantity=struct_order.origQty,
        is_test=False,
        new_client_order_id=struct_order.clientOrderId,
    )
    assert order.symbol == liquid_symbol
    assert order.clientOrderId == struct_order.clientOrderId
    assert order.transactTime > now.timestamp() * 1_000
    assert order.origQty == struct_order.origQty
    assert order.timeInForce == struct_order.timeInForce
    assert order.type == struct_order.type
    assert order.side == struct_order.side


def test_structure_fill(uns_fill, struct_fill):
    assert Fill.structure(uns_fill) == struct_fill


def test_structure_fills(uns_fills, struct_fills):
    assert Fill.structure(uns_fills) == struct_fills


def test_structure_order(api_response, struct_order, env_state_id):
    assert Order.structure({**{"env_state_id": env_state_id}, **api_response}) == struct_order
