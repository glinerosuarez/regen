from typing import Union, Callable
from pathlib import Path

import functools


def delete_file(file: Union[str, Path]) -> None:
    """
    Delete a file.
    :param file: file path or :Path: object.
    """
    Path(file).unlink()


def clean(clean_func: Callable) -> Callable:
    """
    Decorator to execute code after a test function.
    :param clean_func: function to execute after the decorated one.
    :return:
    """
    def decorator_clean(func: Callable):
        @functools.wraps(func)
        def wrapper_clean(*args, **kwargs) -> None:
            try:
                func(*args, **kwargs)
            finally:
                clean_func()
        return wrapper_clean
    return decorator_clean

