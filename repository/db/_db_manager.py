import enum
import json
import logging
from pathlib import Path

import attr
import cattr
import numpy as np
import pendulum
from sqlalchemy.sql.elements import BinaryExpression

from attr import attrs, attrib, define, field
import sqlalchemy.types as types
from typing import List, Optional, Type, Any, Union
from attr.validators import instance_of
from sqlalchemy.exc import IntegrityError

from conf.consts import TimeInForce, OrderType, Side, Position, Action, Algorithm, CryptoAsset, OrderStatus
from repository._dataclass import DataClass, TradingPair
from repository._consts import AccountType, Balance, AccountPermission
from sqlalchemy.dialects.sqlite.pysqlite import SQLiteDialect_pysqlite
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


class DataBaseManager:
    class EngineType(enum.Enum):
        SQLite = "sqlite"
        PostgreSQL = "postgreSQL"

    _mapper_registry = registry()

    @staticmethod
    def _build_engine_string(
        e_type: EngineType,
        db_name: str,
        db_file_location: Optional[Path] = None,
        host: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ) -> str:
        if e_type == DataBaseManager.EngineType.PostgreSQL:
            return f"postgresql+psycopg2://{user}:{password}@{host}:5432/{db_name}"
        elif e_type == DataBaseManager.EngineType.SQLite:
            db_file_location = "." if db_file_location is None else str(db_file_location.absolute())
            db_filename = ":memory:" if db_name == ":memory:" else f"{db_file_location}/{db_name}"
            return f"sqlite+pysqlite:///{db_filename}"
        else:
            raise ValueError(f"unimplemented engine type: {e_type}")

    @staticmethod
    def _create_postgres_engine(
        db_name: str,
        host: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ):
        return create_engine(
            DataBaseManager._build_engine_string(
                e_type=DataBaseManager.EngineType.PostgreSQL, db_name=db_name, host=host, user=user, password=password
            ),
            echo=False,
            future=True,
        )

    @staticmethod
    def _create_sqlite_engine(db_name: str, db_file_location: Union[str, Path]):
        return create_engine(
            DataBaseManager._build_engine_string(DataBaseManager.EngineType.SQLite, db_name, db_file_location),
            echo=False,
            future=True,
            # It's safe to do this because we never update objects from other threads, in fact, we never update.
            connect_args={"check_same_thread": False},
        )

    def __init__(
        self,
        db_name: str,
        engine_type: EngineType = EngineType.SQLite,
        host: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        files_dir: Optional[Path] = Path() / "output",
    ):
        self.db_name = db_name
        self.logger = LoggerFactory.get_file_logger(
            name="sqlalchemy", file_dir=files_dir / "logs", preffix="db", security_level=logging.WARNING
        )

        # Connect to a database or create a new database if it does not exist.
        if engine_type == DataBaseManager.EngineType.SQLite:
            self.engine = DataBaseManager._create_sqlite_engine(db_name, files_dir)
        elif engine_type == DataBaseManager.EngineType.PostgreSQL:
            self.engine = DataBaseManager._create_postgres_engine(db_name, host, user, password)
        session_factory = sessionmaker(bind=self.engine)
        self.session = scoped_session(session_factory)

        # Create tables.
        DataBaseManager._mapper_registry.metadata.create_all(self.engine)

    def insert(self, records: Union[DataClass, List[DataClass]]) -> None:
        """Insert a new row into a SQL table."""

        exception = None

        try:
            if isinstance(records, list):
                self.session.bulk_save_objects(records)
            elif isinstance(records, DataClass):
                self.session.add(records)
            else:
                raise ValueError(f"Unsupported type {type(records)} for records")
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
        conditions: Optional[Union[BinaryExpression, List[BinaryExpression]]] = None,
        function=select,
    ):
        """
        Apply sql.expression and conditions to a table.
        :param table: Table to run the query on.
        :param conditions: Where conditions.
        :param function: SQLAlchemy sql.expression that allows for the where clause.
        :return: SQLAlchemy executable query object.
        """
        if conditions is None:
            sql_statement = function(table)
        elif isinstance(conditions, list):
            sql_statement = function(table).where(and_(*conditions))
        else:
            sql_statement = function(table).where(conditions)

        return sql_statement

    def select(
        self,
        table: Type[DataClass],
        conditions: Optional[Union[BinaryExpression, List[BinaryExpression]]] = None,
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
        self, col: InstrumentedAttribute, condition: Optional[Union[BinaryExpression, bool]] = None
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

    def select_min(
        self, col: InstrumentedAttribute, condition: Optional[Union[BinaryExpression, bool]] = None
    ) -> Optional[Any]:
        """
        Return the smallest value in a column.
        :param col: Column to get the value from.
        :param condition: Binary condition that is used to filter out rows.
        :return: Maximum value in the column.
        """
        sql_statement = select(func.min(col))
        if condition is not None:
            sql_statement = sql_statement.where(condition)
        return self.session.execute(sql_statement).fetchone()[0]

    def delete(
        self,
        table: Type[DataClass],
        conditions: Optional[Union[BinaryExpression, List[BinaryExpression]]] = None,
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

    def count_rows(
        self,
        col: InstrumentedAttribute,
    ) -> int:
        """
        Count rows in a table
        :param col: column whose rows we want to count
        :return: row count
        """
        return self.session.query(col).count()

    def get_last_id(self, table: Type[DataClass]) -> Optional[int]:
        last_record = self.session.query(table).order_by(table.id.desc()).first()
        return None if last_record is None else last_record.id


class _EncodedDataClass(types.UserDefinedType):
    """
    A SQLAlchemy custom type that represents an immutable structure as a json-encoded string.
    Usage: EncodedDataClass(DataClass)
    """

    def __init__(self, type_):
        self.type_ = type_

    def get_col_spec(self, **kw):
        return "JSON"

    def bind_processor(self, dialect):
        def process(value):
            if value is not None:
                value = json.dumps(cattr.unstructure(value))
            return value

        return process

    def result_processor(self, dialect, coltype):
        def process(value):
            if value is not None:
                if isinstance(dialect, SQLiteDialect_pysqlite):
                    value = cattr.structure(json.loads(value), self.type_)
                else:
                    value = cattr.structure(value, self.type_)
            return value

        return process


@DataBaseManager._mapper_registry.mapped
@define(slots=False)
class Fill(DataClass):
    __table__ = Table(
        "fills",
        DataBaseManager._mapper_registry.metadata,
        Column("id", Integer, primary_key=True, nullable=False, autoincrement="auto"),
        Column("order_id", Integer, ForeignKey("orders.id")),
        Column("price", Float),
        Column("qty", Float),
        Column("commission", Float),
        Column("commissionAsset", _EncodedDataClass(CryptoAsset)),
        Column("tradeId", Integer),
    )

    id: int = field(init=False)
    order_id: int = field(init=False)
    price: float = field(converter=float)
    qty: float = field(converter=float)
    commission: float = field(converter=float)
    commissionAsset: CryptoAsset = field(converter=CryptoAsset, validator=instance_of(CryptoAsset))
    tradeId: int = field(converter=int)


@DataBaseManager._mapper_registry.mapped
@define(slots=False)
class Order(DataClass):
    """Data of a placed order."""

    __table__ = Table(
        "orders",
        DataBaseManager._mapper_registry.metadata,
        Column("id", Integer, primary_key=True, nullable=False, autoincrement="auto"),
        Column("env_state_id", Integer, nullable=False, unique=True),
        Column("symbol", _EncodedDataClass(TradingPair)),
        Column("orderId", String),
        Column("orderListId", String),
        Column("clientOrderId", String, unique=True),
        Column("transactTime", Integer),
        Column("price", Float),
        Column("origQty", Float),
        Column("executedQty", Float),
        Column("cummulativeQuoteQty", Float),
        Column("status", Enum(OrderStatus)),
        Column("timeInForce", Enum(TimeInForce)),
        Column("type", Enum(OrderType)),
        Column("side", Enum(Side)),
        Column("workingTime", BigInteger),
        Column("selfTradePreventionMode", String),
    )

    __mapper_args__ = {  # type: ignore
        "properties": {
            "fills": relationship("Fill"),
        }
    }

    id: int = field(init=False)
    env_state_id: int = field(converter=int)
    symbol: TradingPair = field(converter=TradingPair.structure)
    orderId: str = field(converter=str)
    orderListId: str = field(converter=str)  # Unless OCO, value will be -1
    clientOrderId: str = field(converter=str)
    transactTime: int = field(converter=int)  # Timestamp in ms
    price: float = field(converter=float)
    origQty: float = field(converter=float)  # Quantity set in the order
    executedQty: float = field(converter=float)
    cummulativeQuoteQty: float = field(converter=float)
    status: OrderStatus = field(converter=OrderStatus)
    timeInForce: TimeInForce = field(converter=TimeInForce)
    type: OrderType = field(converter=OrderType)
    side: Side = field(converter=Side)
    workingTime: int = field(converter=int)
    selfTradePreventionMode: str = field(converter=str)
    fills: List[Fill] = field(converter=Fill.structure)

    @classmethod
    def structure(cls, data: Union[dict, list]) -> "Order":
        # Override this method because cattrs doesn't support structure this complex scenario.
        return cls(**{a.name: data[a.name] for a in attr.fields(cls) if a.init})


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
        Column("commissionRates", _EncodedDataClass(dict)),
        Column("requireSelfTradePrevention", Boolean),
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
    commissionRates: dict = attrib()
    requireSelfTradePrevention: bool = attrib(converter=bool)
    ts: int = attrib(converter=int, default=pendulum.now().int_timestamp)


@DataBaseManager._mapper_registry.mapped
@attrs
class EnvState(DataClass):
    __table__ = Table(
        "env_state",
        DataBaseManager._mapper_registry.metadata,
        Column("id", Integer, primary_key=True, nullable=False, autoincrement="auto"),
        Column("execution_id", Integer, nullable=False),
        Column("episode_id", Integer, nullable=False),
        Column("tick", BigInteger, nullable=False),
        Column("price", Float, nullable=False),
        Column("position", Enum(Position, name="tradingposition"), nullable=False),
        Column("action", Enum(Action), nullable=False),
        Column("is_trade", Boolean, nullable=False),
        Column("reward", Float, nullable=True),
        Column("cum_reward", Float, nullable=True),
        Column("ts", Float, nullable=False),
    )

    id: int = attrib(init=False)
    execution_id: int = attrib(converter=int)
    episode_id: int = attrib(converter=int)
    tick: int = attrib(converter=int)
    price: float = attrib(converter=float)
    position: Position = attrib()
    action: Action = attrib()
    is_trade: bool = attrib()
    reward: float = attrib()
    cum_reward: float = attrib()
    ts: float = attrib()


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
        Column("open_time", BigInteger, nullable=False, unique=True),
        Column("open_value", Float, nullable=False),
        Column("high", Float, nullable=False),
        Column("low", Float, nullable=False),
        Column("close_value", Float, nullable=False),
        Column("volume", Float, nullable=False),
        Column("close_time", BigInteger, nullable=False, unique=True),
        Column("quote_asset_vol", Float, nullable=False),
        Column("trades", BigInteger, nullable=False),
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
    klines: List[Kline]
    created_at: pendulum.DateTime = field(init=False, converter=pendulum.DateTime)


@DataBaseManager._mapper_registry.mapped
@define(slots=False)
class TrainSettings:
    __table__ = Table(
        "train_settings",
        DataBaseManager._mapper_registry.metadata,
        Column("id", Integer, primary_key=True, nullable=False, autoincrement="auto"),
        Column("execution_id", ForeignKey("execution.id")),
        Column("db_name", String, nullable=False),
        Column("window_size", Integer, nullable=False),
        Column("ticks_per_episode", Integer, nullable=False),
        Column("is_live_mode", Boolean, nullable=False),
        Column("klines_buffer_size", Integer, nullable=False),
        Column("load_from_execution_id", Integer, nullable=True),
        Column("place_orders", Boolean),
    )

    id: int = field(init=False)
    execution_id: int = field(init=False)
    db_name: str
    window_size: int
    ticks_per_episode: int
    is_live_mode: bool
    klines_buffer_size: int
    load_from_execution_id: int
    place_orders: bool


@DataBaseManager._mapper_registry.mapped
@define(slots=False)
class Execution(DataClass):
    __table__ = Table(
        "execution",
        DataBaseManager._mapper_registry.metadata,
        Column("id", Integer, primary_key=True, nullable=False, autoincrement="auto"),
        Column("pair", _EncodedDataClass(TradingPair), nullable=False),
        Column("algorithm", Enum(Algorithm), nullable=False),
        Column("n_steps", BigInteger, nullable=False),
        Column("start", Float, nullable=False, unique=True),
        Column("output_dir", String, nullable=True),
        Column("end", Float, nullable=True, unique=True),
    )

    id: int = field(init=False)
    pair: TradingPair = field(converter=TradingPair.structure, validator=instance_of(TradingPair))
    algorithm: Algorithm
    n_steps: int
    start: float
    output_dir: str
    end: float = field(init=False)
    settings: TrainSettings

    __mapper_args__ = {  # type: ignore
        "properties": {
            "settings": relationship("TrainSettings", uselist=False, backref="Execution"),
        }
    }

    @property
    def load_model_path(self) -> Path:
        return Path(self.output_dir) / str(self.settings.load_from_execution_id) / f"model/{self.algorithm.value}"

    @property
    def load_env_path(self) -> Path:
        return Path(self.output_dir) / str(self.settings.load_from_execution_id) / "env/env.pkl"
