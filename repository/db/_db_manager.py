import json
import cattr
import pendulum
from log import LoggerFactory
from attr import attrs, attrib
import sqlalchemy.types as types
from sqlalchemy.engine import Engine
from typing import List, Optional, Type
from attr.validators import instance_of
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import registry, Session
from consts import TimeInForce, OrderType, Side
from repository._dataclass import DataClass, TradingPair
from repository._consts import Fill, AccountType, Balance, AccountPermission
from sqlalchemy import create_engine, Table, Column, String, Integer, Float, Enum, select, Boolean, BigInteger

_mapper_registry = registry()
_logger = LoggerFactory.get_console_logger(__name__)


class DataBaseManager:
    _engine: Engine = None
    _session: Optional[Session] = None

    @staticmethod
    def create_all():
        _mapper_registry.metadata.create_all(DataBaseManager._engine)

    @staticmethod
    def init_connection(db_name: str) -> None:
        """
        Connect to a database or create a new database if it does not exist.
        :param db_name: Name of the database
        """
        DataBaseManager._engine = create_engine(f"sqlite+pysqlite:///{db_name}", echo=True, future=True)
        DataBaseManager._session = Session(DataBaseManager._engine)

    @staticmethod
    def insert(record: DataClass) -> None:
        """Insert a new row into a SQL table."""
        exception = None
        try:
            DataBaseManager._session.add(record)
            DataBaseManager._session.commit()
        except IntegrityError as ie:
            exception = ie
        finally:
            if exception is not None:
                # If there is an exception rollback the transaction and propagate the error.
                DataBaseManager._session.rollback()
                raise exception

    @staticmethod
    def select(table: Type[DataClass]) -> list:
        """
        Execute a SELECT statement from the SQL Object table.
        :return: a :list: of SQL Object.
        """
        return [data[0] for data in DataBaseManager._session.execute(select(table))]


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


@_mapper_registry.mapped
@attrs
class Order(DataClass):
    """Data of a placed order."""

    __table__ = Table(
        "orders",
        _mapper_registry.metadata,
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

    symbol: TradingPair = attrib(validator=instance_of(TradingPair), converter=TradingPair.from_str)
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


@_mapper_registry.mapped
@attrs
class AccountInfo(DataClass):
    __table__ = Table(
        "account_info",
        _mapper_registry.metadata,
        Column("makerCommission", Float),
        Column("takerCommission", Float),
        Column("buyerCommission", Float),
        Column("sellerCommission", Float),
        Column("canTrade", Boolean),
        Column("canWithdraw", Boolean),
        Column("canDeposit", Boolean),
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
    updateTime: int = attrib(converter=int)
    accountType: AccountType = attrib(converter=AccountType)
    balances: List[Balance] = attrib(converter=Balance.structure)
    permissions: List[AccountPermission] = attrib(converter=AccountPermission._converter)
    ts: int = attrib(converter=int, default=pendulum.now().int_timestamp)