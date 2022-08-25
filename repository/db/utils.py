import asyncio
from typing import AsyncIterator, Iterator

from repository._dataclass import DataClass
from repository.db._db_manager import DataBaseManager


def get_db_generator(db_name: str, table: type[DataClass], page_size: int) -> Iterator[DataClass]:
    """
    Get a generator that returns all the rows in a table
    :param db_name: Name of the database
    :param table: Table from which we'll get the rows.
    :param page_size: Max number of rows to store in memory.
    """
    DataBaseManager.init(db_name)

    def _get_page_generator() -> Iterator[list[DataClass]]:
        offset = 0
        _page = DataBaseManager.select(table, offset=offset, limit=page_size)
        while len(_page) > 0:
            yield _page
            offset += page_size
            _page = DataBaseManager.select(table, offset=offset, limit=page_size)

    for page in _get_page_generator():
        yield from page


async def get_db_async_generator(db_name: str, table: type[DataClass], page_size: int) -> AsyncIterator[DataClass]:
    """
    Get an asynchronous generator that returns all the rows in a table
    :param db_name: Name of the database
    :param table: Table from which we'll get the rows.
    :param page_size: Max number of rows to store in memory.
    """
    DataBaseManager.init(db_name)

    async def select_page(offset: int):
        return await asyncio.to_thread(DataBaseManager.select, table=table, offset=offset, limit=page_size)

    async def _get_page_generator() -> AsyncIterator[list[DataClass]]:
        offset = 0
        _page = await select_page(offset)
        while len(_page) > 0:
            yield _page
            offset += page_size
            _page = await select_page(offset)

    async for page in _get_page_generator():
        for row in page:
            yield row
