import numpy as np
from repository import Repository
from env.model._AbstractModel import AbstractModel


class LiveModel(AbstractModel):

    repository = Repository()

    def _next_observation(self) -> np.ndarray:
        pass
