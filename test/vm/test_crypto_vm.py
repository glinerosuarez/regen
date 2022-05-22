import time

from consts import CryptoAsset
from vm.crypto_vm import CryptoViewModel


def test_crypto_vm():
    vm = CryptoViewModel(CryptoAsset.BNB, CryptoAsset.BUSD, 5)
    # Start the producer
    print("Starting producer")
    vm.reset()
    print("I'm able to keep doing stuff in this thread")
    time.sleep(5)
    print("Oh yeah after 5 secs I'm still able to do other stuff!")
    print(vm.get_observation())

    print("It's over my friend")


if __name__ == "__main__":
    test_crypto_vm()
