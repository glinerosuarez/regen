import pytest
from sqlalchemy.exc import IntegrityError

from test import test_utils
from repository import AccountType
from vm.consts import Position, Action
from repository.db import DataBaseManager, Order, AccountInfo, EnvState

db_name = ":memory:"
data = Order(
    symbol="BNBBUSD",
    orderId="12345",
    orderListId="-1",
    clientOrderId="67890",
    transactTime=10,
    price=400.0,
    origQty=10,
    executedQty=10.0,
    cummulativeQuoteQty=10.0,
    status="FILLED",
    timeInForce="GTC",
    type="LIMIT",
    side="BUY",
    fills=[{"price": 400.0, "qty": 10.0, "commission": 0.001, "commissionAsset": "BUSD"}],
)
data_2 = data.copy(with_={"symbol": "ETHBUSD"})
data_3 = data.copy(with_={"symbol": "BTCUSDT", "orderId": "67890"})
data_4 = data.copy(with_={"symbol": "BTCUSDT", "orderId": "11121", "clientOrderId": "anyid"})

acc_info = AccountInfo(
    makerCommission=0.001,
    takerCommission=0.001,
    buyerCommission=0.001,
    sellerCommission=0.001,
    canTrade=True,
    canWithdraw=True,
    canDeposit=True,
    updateTime=1631587291,
    accountType=AccountType.SPOT,
    balances=[{"asset": "BNB", "free": 1.0, "locked": 0.0}],
    permissions=["SPOT"],
)

env_state = EnvState(
    execution_id=1,
    episode_id=1,
    tick=1,
    price=100.0,
    position=Position.Long,
    action=Action.Sell,
    is_trade=False,
    ts=1651992028.7183151,
)


def tear_down():
    # Clean up
    test_utils.delete_file(db_name)


def test_db_orders():
    # Init db
    DataBaseManager.init_connection(db_name)
    DataBaseManager.create_all()
    DataBaseManager.insert(data)
    # Assert primary key
    with pytest.raises(IntegrityError):
        DataBaseManager.insert(data_2)
    # Assert uniqueness
    with pytest.raises(IntegrityError):
        DataBaseManager.insert(data_3)
    DataBaseManager.insert(data_4)
    # Assertions
    records = DataBaseManager.select_all(Order)
    assert len(records) == 2
    assert records[0] == data
    assert records[1] == data_4


def test_account_info():
    # Init db
    DataBaseManager.init_connection(db_name)
    DataBaseManager.create_all()
    DataBaseManager.insert(acc_info)

    # Assertions
    records = DataBaseManager.select_all(AccountInfo)
    assert records[0] == acc_info


def test_env_state():
    # Init db
    DataBaseManager.init_connection(db_name)
    DataBaseManager.create_all()
    DataBaseManager.insert(env_state)

    # Assertions
    records = DataBaseManager.select_all(EnvState)
    assert records[0] == env_state

    # Test select_max
    assert DataBaseManager.select_max(EnvState.state_id) == "1-1-1"
