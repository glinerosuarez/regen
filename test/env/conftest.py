from typing import List

import pytest

from conf.consts import Action


@pytest.fixture
def actions() -> List[Action]:
    return [
        Action.Sell,
        Action.Sell,
        Action.Sell,
        Action.Sell,
        Action.Buy,
        Action.Buy,
        Action.Sell,
        Action.Buy,
        Action.Buy,
        Action.Buy,
        Action.Buy,
        Action.Sell,
        Action.Sell,
        Action.Buy,
    ]
