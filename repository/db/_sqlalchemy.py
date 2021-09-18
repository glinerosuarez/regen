import json
import cattr
from abc import ABC, abstractmethod
from attr import attrs, attrib
import sqlalchemy.types as types
from typing import List

from repository._consts import Fill
from sqlalchemy.orm import registry
from attr.validators import instance_of
from consts import TradingPair, TimeInForce, OrderType, Side
from sqlalchemy import create_engine, Table, Column, String, Integer, Float, Enum


class SQLObject(ABC):

    @staticmethod
    @abstractmethod
    def _get_name() -> str:
        """Name of the table in SQL."""
        pass

    @staticmethod
    @abstractmethod
    def _get_data_class() -> DataClass:
        """DataClass that represent this SQLObject in python code."""
        pass

    @classmethod
    @abstractmethod
    def _create_table(cls) -> None:
        """Create table for this :SQLObject:."""
        pass

    @classmethod
    def insert(cls, record: DataClass) -> None:
        """Insert a new row into :SQLObject: table."""
        SQLiteManager.insert(cls.get_name(), record.get_types().attrs, record.to_dict())

    @classmethod
    def select(cls) -> List[DataClass]:
        """
        Execute a SELECT statement from the :SQLObject: table.
        :return: a :list: of :SQLObject:.
        """
        cursor: Cursor = SQLiteManager.select(cls.get_data_class().get_types().attrs, cls.get_name())
        cols = [c[0] for c in cursor.description]

        return cls.get_data_class().from_items([DataClass.Items(attrs=cols, values=r) for r in cursor.fetchall()])

    @classmethod
    def drop_table(cls) -> None:
        """Drop the :SQLObject: table."""
        SQLiteManager.drop_table(cls.get_name())


class EncodedDataClass(types.UserDefinedType):
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


engine = create_engine("sqlite+pysqlite:///:memory:", echo=True, future=True)

mapper_registry = registry()


@mapper_registry.mapped
@attrs
class Order:
    """Data of a placed order."""

    __table__ = Table(
        "ORDERS",
        mapper_registry.metadata,
        Column("symbol", EncodedDataClass(TradingPair)),
        Column("orderId", String, primary_key=True),
        Column("orderListId", String),
        Column("clientOrderId", String),
        Column("transactTime", Integer),
        Column("price", Float),
        Column("origQty", Float),
        Column("executedQty", Float),
        Column("cummulativeQuoteQty", Float),
        Column("status", String),
        Column("timeInForce", Enum),
        Column("type", Enum),
        Column("side", Enum),
        Column("fills", EncodedDataClass(List[Fill])),
    )

    symbol: TradingPair = attrib(validator=instance_of(TradingPair), converter=TradingPair.from_str_or_dict)
    orderId: str = attrib(converter=str)
    orderListId: str = attrib(converter=str)  # Unless OCO, value will be -1
    clientOrderId: str = attrib(converter=str)
    transactTime: int = attrib(converter=int)  # Timestamp in ms
    price: float = attrib(converter=float)
    origQty: float = attrib(converter=float)  # Quantity set in the order
    executedQty: float = attrib(converter=float)
    cummulativeQuoteQty: float = attrib(converter=float)
    status: str = attrib(converter=str)
    timeInForce: TimeInForce = attrib(converter=TimeInForce.converter)
    type: OrderType = attrib(converter=OrderType.converter)
    side: Side = attrib(converter=Side.converter)
    fills: list = attrib(converter=Fill.from_dicts)
