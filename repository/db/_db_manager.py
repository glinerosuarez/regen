from sqlite3 import Cursor
from consts import DataClass
from typing import List, Any, Type
from abc import ABC, abstractmethod
from repository.db import SQLiteManager
from repository._consts import OrderRecord, AccountInfo


class SQLObject(ABC):

    @staticmethod
    @abstractmethod
    def get_name() -> str:
        """Name of the table in SQL."""
        pass

    @staticmethod
    @abstractmethod
    def get_data_class() -> DataClass:
        """DataClass that represent this SQLObject in python code."""
        pass

    @classmethod
    def get_supported_types(cls) -> List[Type[Any]]:
        return [dict if issubclass(t, DataClass) else t for t in cls.get_data_class().get_types().types]

    @classmethod
    @abstractmethod
    def create_table(cls) -> None:
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


class DataBaseManager:
    """Perform data base operations."""

    class Orders(SQLObject):
        """SQL operations for :OrderRecord:."""

        @staticmethod
        def get_name() -> str:
            return "ORDERS"

        @staticmethod
        def get_data_class() -> DataClass:
            return OrderRecord

        @classmethod
        def create_table(cls) -> None:
            SQLiteManager.create_table(
                name=cls.get_name(),
                col_names=OrderRecord.get_types().attrs,
                types=cls.get_supported_types(),
                primary_key="orderId",
                unique=["clientOrderId"]
            )

    class AccountInfo(SQLObject):

        @staticmethod
        def get_name() -> str:
            return "ACCOUNT_INFO"

        @staticmethod
        def get_data_class() -> DataClass:
            return AccountInfo

        @classmethod
        def create_table(cls) -> None:
            SQLiteManager.create_table(
                name=cls.get_name(),
                col_names=cls.get_data_class().get_types().attrs,
                types=cls.get_supported_types(),
            )

    @staticmethod
    def init_connection(db_name: str) -> None:
        """
        Connect to a database or create a new database if it does not exist.
        :param db_name: Name of the database
        """
        SQLiteManager.init_connection(db_name)

    @staticmethod
    def close() -> None:
        """Close connection."""
        SQLiteManager.close()
