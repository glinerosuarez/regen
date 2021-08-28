from enum import Enum
from typing import Dict, Any


def remove_none_args(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove key value pairs if value is None.
    :param args: Dict containing possible None values.
    :return: Dict without None values.
    """
    return {
        k: v.value if isinstance(v, Enum) else v
        for k, v in args.items()
        if v is not None
    }
