from datetime import datetime
from enum import Enum
from typing import Dict, Any


def remove_none_args(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove key value pairs if value is None.
    :param args: Dict containing possible None values.
    :return: Dict without None values.
    """
    return {k: v.value if isinstance(v, Enum) else v for k, v in args.items() if v is not None}


def datetime_to_ts_ms(dt: datetime) -> int:
    """
    Convert datetime to timestamp in ms.
    :param dt: datetime
    :return: timestamp in ms
    """
    return int(datetime.timestamp(dt)) * 1000


def ts_ms_to_datetime(ts: int) -> datetime:
    """
    Convert timestamp in ms to datetime
    :param ts: timestamp in ms
    :return: datetime
    """
    return datetime.fromtimestamp(int(ts / 1000))
