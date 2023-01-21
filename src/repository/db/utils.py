import asyncio
from typing import AsyncIterator, Iterator, List, Type

import contextvars

import functools

from repository._dataclass import DataClass
from repository.db._db_manager import DataBaseManager


async def to_thread(func, *args, **kwargs):
    """Asynchronously run function *func* in a separate thread.
    Any *args and **kwargs supplied for this function are directly passed
    to *func*. Also, the current :class:`contextvars.Context` is propogated,
    allowing context variables from the main thread to be accessed in the
    separate thread.
    Return a coroutine that can be awaited to get the eventual result of *func*.
    """
    loop = asyncio.events.get_running_loop()
    ctx = contextvars.copy_context()
    func_call = functools.partial(ctx.run, func, *args, **kwargs)
    return await loop.run_in_executor(None, func_call)


def get_db_generator(db_manager: DataBaseManager, table: Type[DataClass], page_size: int) -> Iterator[DataClass]:
    """
    Get a generator that returns all the rows in a table
    :param db_manager:
    :param table: Table from which we'll get the rows.
    :param page_size: Max number of rows to store in memory.
    """

    def _get_page_generator() -> Iterator[List[DataClass]]:
        offset = 0
        _page = db_manager.select(table, offset=offset, limit=page_size)
        while len(_page) > 0:
            yield _page
            offset += page_size
            _page = db_manager.select(table, offset=offset, limit=page_size)

    for page in _get_page_generator():
        yield from page


async def get_db_async_generator(
    db_manager: DataBaseManager, table: Type[DataClass], page_size: int
) -> AsyncIterator[DataClass]:
    """
    Get an asynchronous generator that returns all the rows in a table
    :param db_manager:
    :param table: Table from which we'll get the rows.
    :param page_size: Max number of rows to store in memory.
    """

    async def select_page(offset: int):
        return await to_thread(db_manager.select, table=table, offset=offset, limit=page_size)

    async def _get_page_generator() -> AsyncIterator[List[DataClass]]:
        offset = 0
        _page = await select_page(offset)
        while len(_page) > 0:
            yield _page
            offset += page_size
            _page = await select_page(offset)

    async for page in _get_page_generator():
        for row in page:
            yield row
