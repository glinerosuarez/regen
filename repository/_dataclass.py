import copy

import cattr
import inspect

from attr import attrs, attrib
from consts import CryptoAsset
from attr.validators import instance_of
from typing import List, Union, Optional


@attrs
class DataClass:
    @classmethod
    def structure(cls, value: Union[dict, list]) -> Union["DataClass", List["DataClass"]]:
        if isinstance(value, list):
            if all(isinstance(e, cls) for e in value):
                return value
            return cattr.structure(value, List[cls])
        elif isinstance(value, dict):
            return cattr.structure(value, cls)
        else:
            raise TypeError(f"type {type(value)} of object {value} is not supported.")

    def to_dict(self) -> dict:
        """Attributes and their corresponding values as a dict."""
        return cattr.unstructure(self)

    def copy(self, with_: dict) -> "DataClass":
        """
        Create a deep copy of this instance.
        :param with_: Properties to replace in the new object.
        """
        attribs = copy.deepcopy(
            {  # Copy only constructor params
                k: v for k, v in self.__dict__.items() if k in inspect.signature(self.__init__).parameters
            }
        )

        for k, v in with_.items():
            attribs[k] = v

        return self.__class__(**attribs)


@attrs
class TradingPair(DataClass):
    """A pair of :CryptoAsset:"""

    base: CryptoAsset = attrib(validator=instance_of(CryptoAsset), converter=CryptoAsset)
    quote: CryptoAsset = attrib(validator=instance_of(CryptoAsset), converter=CryptoAsset)

    @classmethod
    def from_str(cls, string: str) -> Optional["TradingPair"]:
        # First crypto asset str found
        f1 = None
        # Second crypto asset str found
        f2 = None
        # Index of the f1
        first = None
        # Index of the f2
        second = None

        for ca in CryptoAsset:
            # Check if a crypto asset str is found
            index = string.find(ca.value)
            if index != -1:
                # If the first crypto asset str has not been found yet, assign vars
                if first is None:
                    f1 = ca
                    first = index
                # Otherwise assign second finding vars
                elif second is None:
                    f2 = ca
                    second = index
                    # We have all what we need, stop searching
                    break
        else:
            # Return None since we have not found a valid crypto pair
            return None
        # Instantiate TradingPair, first occurrence as base and the other as quote
        instance = cls(base=f1, quote=f2) if first < second else cls(base=f2, quote=f1)
        return instance

    @classmethod
    def structure(cls, value: Union[dict, list, str]) -> Union["DataClass", List["DataClass"]]:
        # In addition to dict and list, this class can also be structured from a string.
        if isinstance(value, cls):
            return value
        try:
            return super().structure(value)
        except TypeError:
            if isinstance(value, str):
                return cls.from_str(value)
            else:
                raise TypeError(f"type {type(value)} of object {value} is not supported.")

    def __str__(self):
        return self.base.value + self.quote.value
