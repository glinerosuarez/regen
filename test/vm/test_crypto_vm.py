# TODO: test with sqlite
"""
import time

import configuration
from consts import CryptoAsset
from repository.db import DataBaseManager, Kline
from consts import Action
from vm.crypto_vm import CryptoViewModel


def test_crypto_vm():
    DataBaseManager._engine = None
    configuration.settings.ticks_per_episode = 3
    db_manager = DataBaseManager(configuration.settings.db_name)

    print(db_manager.select_all(Kline))

    vm = CryptoViewModel(CryptoAsset.BNB, CryptoAsset.BUSD, 5, 100)
    # Start the producer
    print("Starting producer")
    print(f"first obs: {vm.reset()}")

    print("I'm able to keep doing stuff in this thread")
    time.sleep(5)
    print("Oh yeah after 5 secs I'm still able to do other stuff!")
    print(vm.step(Action.Buy))

    print("It's over my friend")
"""
