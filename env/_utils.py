from collections import namedtuple
from typing import List

from matplotlib import pyplot as plt, animation, style

import config
from repository.db import DataBaseManager
from repository.db._db_manager import EnvState
from vm.consts import Action

style.use('fivethirtyeight')


if __name__ == '__main__':

    DataBaseManager.init_connection(config.settings.db_name)

    def animate(i):
        ax1.clear()

        records: List[EnvState] = DataBaseManager.select_all(EnvState)

        xs, ys = list(), list()

        ScatterData = namedtuple("ScatterData", ["ticks", "prices"])
        buys, sells = ScatterData([], []), ScatterData([], [])

        for env_state in records:
            # Prices
            xs.append(env_state.tick)
            ys.append(env_state.price)

            # Trades
            if env_state.is_trade:
                if env_state.action == Action.Buy:
                    buys.ticks.append(env_state.tick)
                    buys.prices.append(env_state.price)
                if env_state.action == Action.Sell:
                    sells.ticks.append(env_state.tick)
                    sells.prices.append(env_state.price)

        ax1.plot(xs, ys, zorder=0)
        ax1.scatter(buys.ticks, buys.prices, color="green", zorder=1)
        ax1.scatter(sells.ticks, sells.prices, color="red", zorder=2)

    fig = plt.figure()
    ax1 = fig.add_subplot(1, 1, 1)

    ani = animation.FuncAnimation(fig, animate, interval=61_000)
    plt.show()
