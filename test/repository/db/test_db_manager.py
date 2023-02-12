import pytest
from sqlalchemy.exc import IntegrityError

from conf.consts import Position, Action
from repository import AccountType
from repository.db import Order, AccountInfo, EnvState, Kline


@pytest.fixture
def env_state() -> EnvState:
    return EnvState(
        execution_id=1,
        episode_id=1,
        tick=1,
        price=100.0,
        position=Position.Long,
        action=Action.Sell,
        is_trade=False,
        reward=0.01,
        cum_reward=0.1,
        ts=1651992028.7183151,
    )


@pytest.fixture
def acc_info() -> AccountInfo:
    return AccountInfo(
        makerCommission=0.001,
        takerCommission=0.001,
        buyerCommission=0.001,
        sellerCommission=0.001,
        canTrade=True,
        canWithdraw=True,
        canDeposit=True,
        brokered=True,
        updateTime=1631587291,
        accountType=AccountType.SPOT,
        balances=[{"asset": "BNB", "free": 1.0, "locked": 0.0}],
        permissions=["SPOT"],
        commissionRates={"maker": "0.00150000", "taker": "0.00150000", "buyer": "0.00000000", "seller": "0.00000000"},
        requireSelfTradePrevention=False,
    )


def test_db_orders(db_manager, orders):
    db_manager.insert(orders[0])
    # Assert primary key
    with pytest.raises(IntegrityError):
        db_manager.insert(orders[1])
    # Assert uniqueness
    with pytest.raises(IntegrityError):
        db_manager.insert(orders[2])
    db_manager.insert(orders[3])
    # Assertions
    records = db_manager.select_all(Order)
    assert len(records) == 2
    assert records[0] == orders[0]
    assert records[1] == orders[3]


def test_account_info(db_manager, acc_info):
    # Init db
    db_manager.insert(acc_info)

    # Assertions
    records = db_manager.select_all(AccountInfo)
    assert records[0] == acc_info


def test_env_state(db_manager, env_state):
    # Init db
    db_manager.insert(env_state)
    # Assertions
    records = db_manager.select_all(EnvState)
    assert records[0] == env_state
    # Test select_max
    assert db_manager.select_max(EnvState.id) == 1


def test_select_with_limit(insert_klines, db_manager):
    assert len(db_manager.select(Kline, limit=2)) == 2
    assert db_manager.select(Kline, limit=2)[1].id == 2


def test_select_with_offset(insert_klines, db_manager):
    assert db_manager.select(Kline, offset=20) == []
    assert db_manager.select(Kline, offset=19)[0].id == 20


def test_delete(insert_klines, db_manager):
    assert db_manager.delete(Kline, [Kline.id > 5, Kline.id % 2 == 0]) == 8
    results = db_manager.select_all(Kline)
    assert [r.id for r in results] == [1, 2, 3, 4, 5, 7, 9, 11, 13, 15, 17, 19]


def test_count_rows(insert_klines, db_manager):
    assert db_manager.count_rows(Kline.id) == 20


def test_get_last_id(insert_klines, db_manager):
    assert db_manager.get_last_id(Kline) == 20
