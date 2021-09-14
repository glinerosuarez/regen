import sqlite3
from enum import Enum
from log import LoggerFactory
from sqlite3 import Connection, Cursor
from typing import List, Callable, Any, Type, Dict, Optional, Iterable


def _register_types() -> None:
    """
    Register adapters and converters that are used to parse commonly used types to their string representation so that
    they can be stored in a table.
    """
    def _dict_to_str(d: dict) -> str:
        """Convert a dict object to string."""
        return str({k: str(v) for k, v in d.items()})

    def _adapt_list(lst: list) -> str:
        """Adapt list objects to SQLite type."""
        lst_str = [
            _dict_to_str(e) if isinstance(e, dict) else f"'{str(e)}'" if isinstance(e, Enum) else str(e)
            for e in lst
        ]
        return f"[{','.join(lst_str)}]"

    def _convert_list(v: bytes) -> List[str]:
        """Convert SQLite string to python list."""
        return eval(v)

    def _adapt_dict(dc: dict):
        """Adapt :dict: objects to SQLite type."""
        return _dict_to_str(dc)

    def _convert_dict(dc: bytes) -> dict:
        """Convert SQLite string to :dict:."""
        return eval(dc)

    def _register_type(_type: Type[Any], adapter: Callable, sql_name: str, converter: Callable) -> None:
        """
        Register a python type so that it can be stored as a SQLite type.
        :param _type: python type.
        :param adapter: callable to adapt a python type into a string.
        :param sql_name: SQLite name to create.
        :param converter: callable to convert a string into a python type.
        """
        sqlite3.register_adapter(_type, adapter)
        sqlite3.register_converter(sql_name, converter)
        LoggerFactory.get_console_logger(__name__).info("types ARRAY and MAP successfully registered.")

    _register_type(list, adapter=_adapt_list, sql_name="ARRAY", converter=_convert_list)
    _register_type(dict, adapter=_adapt_dict, sql_name="MAP", converter=_convert_dict)


class SQLiteManager:
    """Perform SQLite operations."""
    _register_types()

    conn: Connection = None
    db_name: str = None

    @staticmethod
    def _map_type(t: Type[Any]) -> str:
        """Map a python type to its corresponding SQLite type."""
        mappings = {int: "INTEGER", float: "REAL", bytes: "BLOB", list: "ARRAY", dict: "MAP"}

        for k, v in mappings.items():
            if issubclass(t, k):
                return v
        else:
            return "TEXT" if t else "NULL"

    @staticmethod
    def init_connection(db_name: str) -> None:
        """
        Creates a new connection to a db :db_name, it creates the db if it does not exist.
        :param db_name: name of the db, can be :memory: to create the db in RAM.
        """
        SQLiteManager.db_name = db_name
        SQLiteManager.conn = sqlite3.connect(database=db_name, detect_types=sqlite3.PARSE_DECLTYPES)

    @staticmethod
    def close():
        """Close connection."""
        SQLiteManager.conn.close()

    @staticmethod
    def _execute(sql: str, placeholders: Optional[Dict[str, Any]] = None) -> Cursor:
        """
        Execute a query and commit changes.
        :param sql: query as a string.
        """
        with SQLiteManager.conn as conn:
            if placeholders:
                return conn.execute(sql, placeholders)
            else:
                return conn.execute(sql)

    @staticmethod
    def create_table(
            name: str,
            col_names: Iterable[str],
            types: Iterable[Type[Any]],
            primary_key: Optional[str] = None,
            unique: Optional[Iterable[str]] = None,
            exists_ok: bool = True,
    ) -> None:
        """
        Create a new table in the current database.
        :param name: name of the table to create.
        :param col_names: a list of column names to define for the table.
        :param types: a list of corresponding types for the columns.
        :param primary_key: name of the column that should be considered as the primary key.
        :param unique:
        :param exists_ok: True for aborting the operation if the table already exists.
        """
        if unique is None:
            unique = []

        columns = ', '.join(
            [
                (
                    c
                    + ' '
                    + SQLiteManager._map_type(t)
                    + f"{' NOT NULL PRIMARY KEY' if c == primary_key else ''}"
                    + f"{' UNIQUE' if c in unique else ''}"
                 )
                for c, t in zip(col_names, types)
            ]
        )
        sql = f"""CREATE TABLE {"IF NOT EXISTS" if exists_ok else ""} {name} ({columns});"""
        SQLiteManager._execute(sql)

    @staticmethod
    def select(columns: List[str], table: str) -> Cursor:
        """
        Run a select query.
        :param columns: names of the columns to select.
        :param table: name of the table to select from.
        :return: cursor objects with the results.
        """
        return SQLiteManager._execute(f"""SELECT {','.join(columns)} FROM {table}""")

    @staticmethod
    def insert(table: str, col_names: Iterable[str], values: Dict[str, Any]) -> None:
        """
        Insert a new row into a table.
        :param table: table name to insert the new row into.
        :param col_names: name of the column where values will be inserted into.
        :param values: values for the new row.
        :return:
        """
        cols = ", ".join(col_names)
        placeholders = ", ".join([":" + i for i in col_names])
        SQLiteManager._execute(f"""INSERT INTO {table} ({cols}) VALUES ({placeholders})""", values)

    @staticmethod
    def drop_table(table: str) -> None:
        """Drop a table from the current database."""
        SQLiteManager._execute(f"""DROP TABLE {table}""")
