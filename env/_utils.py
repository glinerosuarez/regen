from matplotlib import pyplot as plt, animation, style

import config
from repository.db import DataBaseManager
from repository.db._db_manager import EnvState


style.use('fivethirtyeight')


if __name__ == '__main__':

    DataBaseManager.init_connection(config.settings.db_name)

    def animate(i):
        records = DataBaseManager.select_all(EnvState)

        xs, ys = list(), list()

        for env_state in records:
            xs.append(env_state.tick)
            ys.append(env_state.price)

        ax1.clear()
        ax1.plot(xs, ys)


    fig = plt.figure()
    ax1 = fig.add_subplot(1, 1, 1)

    ani = animation.FuncAnimation(fig, animate, interval=61_000)
    plt.show()
