# TODO: fix this test
"""def test_last_trade_price_between_episodes(insert_klines_2ep, vm, actions, window_size):
    vm.reset()
    for i, a in enumerate(actions):
        obs, reward, done, _ = vm.step(a)
        if done:
            last_price = vm.last_price
            last_trade_price = vm.last_trade_price
            break

    vm.reset()
    assert i == 9 - window_size
    assert last_price == vm.last_price
    assert last_trade_price == vm.last_trade_price"""
