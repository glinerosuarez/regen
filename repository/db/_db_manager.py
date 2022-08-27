import json

import cattr
import numpy as np
import pendulum
from sqlalchemy.sql.elements import BinaryExpression

from attr import attrs, attrib, define, field
import sqlalchemy.types as types
from sqlalchemy.engine import Engine
from typing import List, Optional, Type, Any, Callable
from attr.validators import instance_of
from sqlalchemy.exc import IntegrityError
from consts import TimeInForce, OrderType, Side
from repository._dataclass import DataClass, TradingPair
from repository._consts import Fill, AccountType, Balance, AccountPermission
from sqlalchemy.orm import registry, InstrumentedAttribute, relationship, scoped_session, sessionmaker
from sqlalchemy import (
    create_engine,
    Table,
    Column,
    String,
    Integer,
    Float,
    Enum,
    select,
    delete,
    Boolean,
    BigInteger,
    func,
    and_,
    ForeignKey,
    DateTime,
)

from log import LoggerFactory
from vm.consts import Position, Action


class DataBaseManager:

    _engine: Optional[Engine] = None
    _mapper_registry = registry()

    def __init__(self, db_name: str):
        """
        :param db_name: Name of the database
        """
        self.db_name = db_name

        # TODO: It seems this function is not working, I'm not seeing the log files created
        self.logger = LoggerFactory.get_file_logger(name="sqlalchemy", filename="db")

        # Connect to a database or create a new database if it does not exist.
        if DataBaseManager._engine is None:
            DataBaseManager._engine = create_engine(
                f"sqlite+pysqlite:///{self.db_name}",
                echo=False,
                future=True,
                # It's safe to do this because we never update objects from other threads, in fact, we never update.
                connect_args={"check_same_thread": False},
            )
        session_factory = sessionmaker(bind=DataBaseManager._engine)
        self.session = scoped_session(session_factory)

        # Create tables.
        DataBaseManager._mapper_registry.metadata.create_all(DataBaseManager._engine)

    def insert(self, record: DataClass) -> None:
        """Insert a new row into a SQL table."""
        exception = None
        try:
            self.session.add(record)
            self.session.commit()
        except IntegrityError as ie:
            exception = ie
        finally:
            if exception is not None:
                # If there is an exception rollback the transaction and propagate the error.
                self.session.rollback()
                raise exception

    @staticmethod
    def _apply_conditions(
        table: Type[DataClass],
        conditions: Optional[BinaryExpression | list[BinaryExpression]] = None,
        function: Callable = select,
    ):
        """
        Apply sql.expression and conditions to a table.
        :param table: Table to run the query on.
        :param conditions: Where conditions.
        :param function: SQLAlchemy sql.expression that allows for the where clause.
        :return: SQLAlchemy executable query object.
        """
        match conditions:
            case None:
                sql_statement = function(table)
            case [*cond]:
                sql_statement = function(table).where(and_(*cond))
            case _:
                sql_statement = function(table).where(conditions)

        return sql_statement

    def select(
        self,
        table: Type[DataClass],
        conditions: Optional[BinaryExpression | list[BinaryExpression]] = None,
        offset: int = 0,
        limit: int = 0,
    ) -> list:
        """
        Execute a SELECT statement from the SQL Object table.
        :return: a :list: of SQL Object.
        """
        sql_statement = DataBaseManager._apply_conditions(table, conditions)

        if offset != 0:
            sql_statement = sql_statement.offset(offset)

        if limit != 0:
            sql_statement = sql_statement.limit(limit)

        return [data[0] for data in self.session.execute(sql_statement)]

    def select_all(self, table: Type[DataClass]) -> list:
        """
        Execute a SELECT * statement from the SQL Object table.
        :return: a :list: of SQL Object.
        """
        return [data[0] for data in self.session.execute(select(table))]

    def select_max(
        self, col: InstrumentedAttribute, condition: Optional[BinaryExpression | bool] = None
    ) -> Optional[Any]:
        """
        Return the biggest value in a column.
        :param col: Column to get the value from.
        :param condition: Binary condition that is used to filter out rows.
        :return: Maximum value in the column.
        """
        sql_statement = select(func.max(col))
        if condition is not None:
            sql_statement = sql_statement.where(condition)
        return self.session.execute(sql_statement).fetchone()[0]

    def delete(
        self,
        table: Type[DataClass],
        conditions: Optional[BinaryExpression | list[BinaryExpression]] = None,
        commit: bool = False,
    ) -> int:
        """
        Delete rows.
        :param table: Table from which rows will be deleted.
        :param conditions: Condition to filter rows to delete.
        :param commit: whether to commit changes or not.
        :return: Number of rows to delete or deleted if commit == True.
        """
        query = DataBaseManager._apply_conditions(table, conditions, function=delete)
        rowcount = self.session.execute(query).rowcount

        if commit is True:
            self.session.commit()

        return rowcount


class _EncodedDataClass(types.UserDefinedType):
    """
    A SQLAlchemy custom type that represents an immutable structure as a json-encoded string.
    Usage: EncodedDataClass(DataClass)
    """

    def __init__(self, type_):
        self.type_ = type_

    def get_col_spec(self, **kw):
        return "DATA"

    def bind_processor(self, dialect):
        def process(value):
            if value is not None:
                value = json.dumps(cattr.unstructure(value))
            return value

        return process

    def result_processor(self, dialect, coltype):
        def process(value):
            if value is not None:
                value = cattr.structure(json.loads(value), self.type_)
            return value

        return process


@DataBaseManager._mapper_registry.mapped
@attrs
class Order(DataClass):
    """Data of a placed order."""

    __table__ = Table(
        "orders",
        DataBaseManager._mapper_registry.metadata,
        Column("symbol", _EncodedDataClass(TradingPair)),
        Column("orderId", String, primary_key=True),
        Column("orderListId", String),
        Column("clientOrderId", String, unique=True),
        Column("transactTime", Integer),
        Column("price", Float),
        Column("origQty", Float),
        Column("executedQty", Float),
        Column("cummulativeQuoteQty", Float),
        Column("status", String),
        Column("timeInForce", Enum(TimeInForce)),
        Column("type", Enum(OrderType)),
        Column("side", Enum(Side)),
        Column("fills", _EncodedDataClass(List[Fill])),
    )

    symbol: TradingPair = attrib(validator=instance_of(TradingPair), converter=TradingPair.structure)
    orderId: str = attrib(converter=str)
    orderListId: str = attrib(converter=str)  # Unless OCO, value will be -1
    clientOrderId: str = attrib(converter=str)
    transactTime: int = attrib(converter=int)  # Timestamp in ms
    price: float = attrib(converter=float)
    origQty: float = attrib(converter=float)  # Quantity set in the order
    executedQty: float = attrib(converter=float)
    cummulativeQuoteQty: float = attrib(converter=float)
    status: str = attrib(converter=str)
    timeInForce: TimeInForce = attrib(converter=TimeInForce)
    type: OrderType = attrib(converter=OrderType)
    side: Side = attrib(converter=Side)
    fills: List[Fill] = attrib(converter=Fill.structure)


@DataBaseManager._mapper_registry.mapped
@attrs
class AccountInfo(DataClass):
    __table__ = Table(
        "account_info",
        DataBaseManager._mapper_registry.metadata,
        Column("makerCommission", Float),
        Column("takerCommission", Float),
        Column("buyerCommission", Float),
        Column("sellerCommission", Float),
        Column("canTrade", Boolean),
        Column("canWithdraw", Boolean),
        Column("canDeposit", Boolean),
        Column("brokered", Boolean),
        Column("updateTime", BigInteger),
        Column("accountType", Enum(AccountType)),
        Column("balances", _EncodedDataClass(List[Balance])),
        Column("permissions", _EncodedDataClass(List[AccountPermission])),
        Column("ts", BigInteger, primary_key=True),
    )

    # When you add an order that doesn't match existing offers, you add liquidity to the market and are charged a maker
    # fee
    makerCommission: float = attrib(converter=float)
    # When you create an order that is immediately matched with already existing orders, you're a taker because you take
    # liquidity from the market
    takerCommission: float = attrib(converter=float)
    buyerCommission: float = attrib(converter=float)
    sellerCommission: float = attrib(converter=float)
    canTrade: bool = attrib(converter=bool)
    canWithdraw: bool = attrib(converter=bool)
    canDeposit: bool = attrib(converter=bool)
    brokered: bool = attrib(converter=bool)
    updateTime: int = attrib(converter=int)
    accountType: AccountType = attrib(converter=AccountType)
    balances: List[Balance] = attrib(converter=Balance.structure)
    permissions: List[AccountPermission] = attrib(converter=AccountPermission._converter)
    ts: int = attrib(converter=int, default=pendulum.now().int_timestamp)


@DataBaseManager._mapper_registry.mapped
@attrs
class EnvState(DataClass):
    __table__ = Table(
        "env_state",
        DataBaseManager._mapper_registry.metadata,
        Column("state_id", String, primary_key=True, nullable=False),
        Column("execution_id", Integer, nullable=False),
        Column("episode_id", Integer, nullable=False),
        Column("tick", BigInteger, nullable=False),
        Column("price", Float, nullable=False),
        Column("position", Enum(Position), nullable=False),
        Column("action", Enum(Action), nullable=False),
        Column("is_trade", Boolean, nullable=False),
        Column("ts", Float, nullable=False),
    )

    execution_id: int = attrib(converter=int)
    episode_id: int = attrib(converter=int)
    tick: int = attrib(converter=int)
    state_id: str = attrib(init=False)
    price: float = attrib(converter=float)
    position: Position = attrib()
    action: Action = attrib()
    is_trade: bool = attrib()
    ts: float = attrib()

    @state_id.default
    def _id(self):
        return "-".join([str(self.execution_id), str(self.episode_id), str(self.tick)])


# TODO: Create a new column which is a concatenation of obs_id and kline_id, this column must be unique
ObservationKline = Table(
    "ObservationKline",
    DataBaseManager._mapper_registry.metadata,
    Column("id", Integer, primary_key=True, autoincrement="auto"),
    Column("obs_id", Integer, ForeignKey("observation.id")),
    Column("kline_id", Integer, ForeignKey("kline.id")),
    Column("created_at", DateTime, server_default=func.now()),
)


@DataBaseManager._mapper_registry.mapped
@attrs
class Kline(DataClass):
    __table__ = Table(
        "kline",
        DataBaseManager._mapper_registry.metadata,
        Column("id", Integer, primary_key=True, nullable=False, autoincrement="auto"),
        Column("pair", _EncodedDataClass(TradingPair)),
        Column("open_time", Integer, nullable=False, unique=True),
        Column("open_value", Float, nullable=False),
        Column("high", Float, nullable=False),
        Column("low", Float, nullable=False),
        Column("close_value", Float, nullable=False),
        Column("volume", Float, nullable=False),
        Column("close_time", Integer, nullable=False, unique=True),
        Column("quote_asset_vol", Float, nullable=False),
        Column("trades", Integer, nullable=False),
        Column("taker_buy_base_vol", Float, nullable=False),
        Column("taker_buy_quote_vol", Float, nullable=False),
        Column("created_at", DateTime, server_default=func.now()),
    )

    id: int = attrib(init=False)
    pair: TradingPair = attrib(converter=TradingPair.structure, validator=instance_of(TradingPair))
    open_time: int = attrib(converter=int)
    open_value: float = attrib(converter=float)
    high: float = attrib(converter=float)
    low: float = attrib(converter=float)
    close_value: float = attrib(converter=float)
    volume: float = attrib(converter=float)
    close_time: int = attrib(converter=int)
    quote_asset_vol: float = attrib(converter=float)  # Volume measured in the units of the second part of the pair.
    trades: int = attrib(converter=int)
    # Explanation: https://dataguide.cryptoquant.com/market-data/taker-buy-sell-volume-ratio
    taker_buy_base_vol: float = attrib(converter=float)
    taker_buy_quote_vol: float = attrib(converter=float)
    created_at: pendulum.DateTime = attrib(init=False, converter=pendulum.DateTime)

    def to_numpy(self) -> np.ndarray:
        values = vars(self)
        return np.array([values[at.name] for at in list(self.__class__.__attrs_attrs__)])


@DataBaseManager._mapper_registry.mapped
@define(slots=False)
class Observation(DataClass):
    __table__ = Table(
        "observation",
        DataBaseManager._mapper_registry.metadata,
        Column("id", Integer, primary_key=True, nullable=False, autoincrement="auto"),
        Column("execution_id", String, nullable=False),
        Column("episode_id", Integer, nullable=False),
        Column("created_at", DateTime, server_default=func.now()),
    )

    __mapper_args__ = {  # type: ignore
        "properties": {
            "klines": relationship("Kline", secondary=ObservationKline),
        }
    }

    id: int = field(init=False)
    execution_id: str
    episode_id: int
    klines: list[Kline]
    created_at: pendulum.DateTime = field(init=False, converter=pendulum.DateTime)
