import pytest
from sqlalchemy.exc import IntegrityError
from repository.db._sqlalchemy import DataBaseManager, Order


db_name = "test_db"

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
    records = DataBaseManager.select(Order)
    assert len(records) == 2
    assert records[0] == data
    assert records[1] == data_4

"""def tear_down():
    # Clean up
    test_utils.delete_file(db_name)


@clean(tear_down)
def test_db_orders():
    # Init db
    DataBaseManager.init_connection(db_name)
    DataBaseManager.Orders.create_table()
    DataBaseManager.Orders.insert(data)
    # Assert primary key
    with pytest.raises(IntegrityError):
        DataBaseManager.Orders.insert(data_2)
    # Assert uniqueness
    with pytest.raises(IntegrityError):
        DataBaseManager.Orders.insert(data_3)
    DataBaseManager.Orders.insert(data_4)
    # Assertions
    records = DataBaseManager.Orders.select()
    assert records[0] == data
    assert records[1] == data_4


acc_info = AccountInfo(
    makerCommission=.001,
    takerCommission=.001,
    buyerCommission=.001,
    sellerCommission=.001,
    canTrade=True,
    canWithdraw=True,
    canDeposit=True,
    updateTime=1631587291,
    accountType=AccountType.SPOT,
    balances=[Balance(CryptoAsset.BNB, 1.0, 0.0)],
    permissions=[AccountPermission.SPOT]
)


@clean(tear_down)
def test_account_info():
    # Init db
    DataBaseManager.init_connection(db_name)
    DataBaseManager.AccountInfo.create_table()
    DataBaseManager.AccountInfo.insert(acc_info)

    # Assertions
    records = DataBaseManager.AccountInfo.select()
    assert records[0] == acc_info"""



