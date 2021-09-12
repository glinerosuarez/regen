from typing import List
from sqlite3 import Cursor
from consts import DataClass
from repository.db import SQLiteManager
from repository._consts import OrderRecord


class DataBaseManager:
    """Perform data base operations."""

    class Table:
        """Table names."""
        ORDERS = "orders"

    @staticmethod
    def init_connection(db_name: str) -> None:
        """
        Connect to a database or create a new database if it does not exist.
        :param db_name: Name of the database
        """
        SQLiteManager.init_connection(db_name)

    @staticmethod
    def create_orders_table() -> None:
        types = [dict if issubclass(t, DataClass) else t for t in OrderRecord.get_types().types]
        SQLiteManager.create_table(DataBaseManager.Table.ORDERS, OrderRecord.get_types().attrs, types)

    @staticmethod
    def insert_order(order: OrderRecord) -> None:
        SQLiteManager.insert(DataBaseManager.Table.ORDERS, order.get_types().attrs, order.to_dict())

    @staticmethod
    def select_orders() -> List[OrderRecord]:
        cursor: Cursor = SQLiteManager.select(OrderRecord.get_types().attrs, DataBaseManager.Table.ORDERS)
        cols = [c[0] for c in cursor.description]

        return OrderRecord.from_items([
            DataClass.Items(attrs=cols, values=r)
            for r in cursor.fetchall()
        ])

    @staticmethod
    def drop_orders() -> None:
        SQLiteManager.drop_table(DataBaseManager.Table.ORDERS)

    @staticmethod
    def close() -> None:
        """Close connection."""
        SQLiteManager.close()
