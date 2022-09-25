import copy

import pytest
from sqlalchemy.exc import IntegrityError

import conf
from conf.consts import Position, Action, CryptoAsset
from repository._dataclass import TradingPair
from test import test_utils
from repository import AccountType, Observation
from repository.db import DataBaseManager, Order, AccountInfo, EnvState, Kline

db_name = ":memory:"
conf.settings.execution_id = 1
db_manager = DataBaseManager(db_name)
db_manager2 = DataBaseManager(db_name)

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
    brokered=True,
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
    db_manager.insert(data)
    # Assert primary key
    with pytest.raises(IntegrityError):
        db_manager.insert(data_2)
    # Assert uniqueness
    with pytest.raises(IntegrityError):
        db_manager.insert(data_3)
    db_manager.insert(data_4)
    # Assertions
    records = db_manager.select_all(Order)
    assert len(records) == 2
    assert records[0] == data
    assert records[1] == data_4


def test_account_info():
    # Init db
    db_manager.insert(acc_info)

    # Assertions
    records = db_manager.select_all(AccountInfo)
    assert records[0] == acc_info


def test_env_state():
    # Init db
    db_manager.insert(env_state)

    # Assertions
    records = db_manager.select_all(EnvState)
    assert records[0] == env_state

    # Test select_max
    assert db_manager.select_max(EnvState.state_id) == "1-1-1"


kline = Kline(
    pair=TradingPair(CryptoAsset.BNB, CryptoAsset.BUSD),
    open_time=123456,
    open_value=100,
    high=110,
    low=90,
    close_value=103,
    volume=1_000,
    close_time=123457,
    quote_asset_vol=500,
    trades=20,
    taker_buy_base_vol=700,
    taker_buy_quote_vol=600,
)
kline2 = kline.copy(with_=dict(trades=45, open_time=134567, close_time=234567))
kline3 = kline.copy(with_=dict(trades=101, open_time=334567, close_time=434567))
obs = Observation(execution_id=1, episode_id=1, klines=[kline, kline2])
obs1 = copy.deepcopy(obs)


def test_obs_kline_relationship():

    db_manager2.insert(obs1)
    db_manager2.insert(kline3)
    obs = db_manager2.select_all(Observation)
    assert len(obs[0].klines) == 2
    assert len(db_manager2.select_all(Kline)) == 3


def test_select_with_limit():
    # Insert obs
    obs.klines = []

    for i in range(2, 11):
        db_manager2.insert(obs.copy(with_={"episode_id": i}))

    assert len(db_manager2.select(Observation, limit=2)) == 2
    assert db_manager2.select(Observation, limit=2)[1].episode_id == 2


def test_select_with_offset():
    assert db_manager.select(Observation, offset=10) == []
    obs1.episode_id = 10
    assert db_manager.select(Observation, offset=9)[0].episode_id == 10
    obs1.episode_id = 1


def test_delete():
    assert db_manager2.delete(Observation, [Observation.episode_id > 5, Observation.episode_id % 2 == 0]) == 3
    results = db_manager.select_all(Observation)
    assert [r.episode_id for r in results] == [1, 2, 3, 4, 5, 7, 9]
