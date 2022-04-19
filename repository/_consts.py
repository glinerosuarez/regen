import enum
from typing import Union
from attr import attrs, attrib
from consts import CryptoAsset
from repository._dataclass import DataClass


class AccountType(enum.Enum):
    SPOT = "SPOT"


class AccountPermission(enum.Enum):
    @classmethod
    def _converter(cls, obj: Union[list, "AccountPermission"]):
        if isinstance(obj, list):
            return [cls(o) for o in obj]
        elif isinstance(obj, cls):
            return obj
        elif isinstance(obj, str):
            return cls(obj)

    SPOT = "SPOT"


class Interval(enum.Enum):
    M_1 = "1m"
    M_5 = "5m"
    H_1 = "1h"
    D_1 = "1d"


@attrs
class Fill(DataClass):
    price: float = attrib(converter=float)
    qty: float = attrib(converter=float)
    commission: float = attrib(converter=float)
    commissionAsset: CryptoAsset = attrib(converter=CryptoAsset)


@attrs
class Balance(DataClass):
    asset: CryptoAsset = attrib(converter=CryptoAsset)
    free: float = attrib(converter=float)
    locked: float = attrib(converter=float)


@attrs
class AvgPrice:
    mins: int = attrib(converter=int)  # Minutes to compute average
    price: float = attrib(converter=float)
