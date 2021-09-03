import numpy as np
from abc import ABCMeta, abstractmethod


class AbstractModel(metaclass=ABCMeta):

    @abstractmethod
    def _next_observation(self) -> np.ndarray:
        raise NotImplementedError
