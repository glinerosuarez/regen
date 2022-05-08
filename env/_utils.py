from matplotlib import pyplot as plt, animation, style

style.use('fivethirtyeight')


if __name__ == '__main__':

    def animate(i):
        with open('graph_data.txt', 'r', encoding="utf-8") as data_file:
            graph_data = data_file.read()
            lines = graph_data.split('\n')

        xs, ys = list(), list()

        for line in lines:
            if len(line) > 1:
                x, y = line.split(",")
                xs.append(int(x))
                ys.append(float(y))

        ax1.clear()
        ax1.plot(xs, ys)


    fig = plt.figure()
    ax1 = fig.add_subplot(1, 1, 1)

    ani = animation.FuncAnimation(fig, animate, interval=61_000)
    plt.show()
