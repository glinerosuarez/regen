from repository._consts import OrderRecord
from repository.db._db_manager import DataBaseManager


data = OrderRecord(
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
data_2 = data.copy(_with={"symbol": "ETHBUSD"})
data_3 = data.copy(_with={"symbol": "BTCUSDT"})


def test_db_manager():
    # Init db
    DataBaseManager.init_connection("test_db")
    DataBaseManager.register_types()
    DataBaseManager.create_orders_table()
    DataBaseManager.insert_order(data)
    DataBaseManager.insert_order(data_2)
    DataBaseManager.insert_order(data_3)
    # Assertions
    records = DataBaseManager.select_orders()
    assert records[0] == data
    assert records[1] == data_2
    assert records[2] == data_3
    # Clean up
    DataBaseManager.drop_orders()
