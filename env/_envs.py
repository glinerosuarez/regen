import random
import gym
import numpy as np
from gym import spaces
from attr import attrs, attrib
from consts import EnvConsts, CryptoAsset
from env._render import StockTradingGraph


@attrs(auto_attribs=True)
class CryptoTradingEnv(gym.Env):
    """Crypto asset trading environment that follows gym interface."""

    # The crypto asset we want to accumulate
    main_asset: CryptoAsset
    # The crypto asset we trade our main asset against
    asset_against: CryptoAsset
    # Actions of the format Buy x%, Sell x%, Hold, etc.
    action_space: spaces.Box = attrib(
        init=False, default=spaces.Box(low=np.array([0, 0]), high=np.array([3, 1]), dtype=np.float16)
    )
    # Prices contains the OHCL values for the last five prices
    observation_space: spaces.Box = spaces.Box(low=0, high=1, shape=(6, 6), dtype=np.float16)

    def _next_observation(self):
        # Get the data points for the last 5 days and scale to between 0-1
        frame = np.array(
            [
                self.df.loc[self.current_step : self.current_step + 5, "Open"].values / EnvConsts.MAX_SHARE_PRICE,
                self.df.loc[self.current_step : self.current_step + 5, "High"].values / EnvConsts.MAX_SHARE_PRICE,
                self.df.loc[self.current_step : self.current_step + 5, "Low"].values / EnvConsts.MAX_SHARE_PRICE,
                self.df.loc[self.current_step : self.current_step + 5, "Close"].values / EnvConsts.MAX_SHARE_PRICE,
                self.df.loc[self.current_step : self.current_step + 5, "Volume"].values / EnvConsts.MAX_NUM_SHARES,
            ]
        )
        # Append additional data and scale each value to between 0-1
        obs = np.append(
            frame,
            [
                [
                    self.balance / EnvConsts.MAX_ACCOUNT_BALANCE,
                    self.max_net_worth / EnvConsts.MAX_ACCOUNT_BALANCE,
                    self.shares_held / EnvConsts.MAX_NUM_SHARES,
                    self.cost_basis / EnvConsts.MAX_SHARE_PRICE,
                    self.total_shares_sold / EnvConsts.MAX_NUM_SHARES,
                    self.total_sales_value / (EnvConsts.MAX_NUM_SHARES * EnvConsts.MAX_SHARE_PRICE),
                ]
            ],
            axis=0,
        )
        return obs

    def _take_action(self, action):
        # We select at random the price at which we perform the buy/sell transaction
        current_price = random.uniform(self.df.loc[self.current_step, "Open"], self.df.loc[self.current_step, "Close"])

        # Check if we buy, sell or hold
        action_type = action[0]
        # How much, extraneous when holding
        amount = action[1]

        if action_type < 1:
            # Buy amount % of balance in shares
            # The max number of assets we can buy at the current price
            total_possible = int(self.balance / current_price)
            # Quantity to buy
            shares_bought = int(total_possible * amount)
            # How much did the shares we already have cost
            prev_cost = self.cost_basis * self.shares_held
            # How much do the shares in this transaction cost
            additional_cost = shares_bought * current_price
            # Subtract the cost of this transaction from our balance
            self.balance -= additional_cost
            # Update the total cost of all the assets we have
            self.cost_basis = (prev_cost + additional_cost) / (self.shares_held + shares_bought)
            # Update the total number of shares we have
            self.shares_held += shares_bought
            if shares_bought > 0:
                self.trades.append(
                    {"step": self.current_step, "shares": shares_bought, "total": additional_cost, "type": "buy"}
                )

        elif action_type < 2:
            # Sell amount % of shares held
            # The number of shares we are selling
            shares_sold = int(self.shares_held * amount)
            # Update balance, adding the money we get for selling
            self.balance += shares_sold * current_price
            # Subtract the shares sold from the count of assets we have
            self.shares_held -= shares_sold
            # Increase the total count of shares sold
            self.total_shares_sold += shares_sold
            # update the sum of the money we've earned by selling
            self.total_sales_value += shares_sold * current_price

            if shares_sold > 0:
                self.trades.append(
                    {
                        "step": self.current_step,
                        "shares": shares_sold,
                        "total": shares_sold * current_price,
                        "type": "sell",
                    }
                )

        # Update our net worth
        self.net_worth = self.balance + self.shares_held * current_price

        # Update max_net_worth if we've hit an ATH
        if self.net_worth > self.max_net_worth:
            self.max_net_worth = self.net_worth

        # If we don't have any shares, set cost_basis to 0
        if self.shares_held == 0:
            self.cost_basis = 0

    def _render_to_file(self, filename="render.txt"):
        profit = self.net_worth - EnvConsts.INITIAL_ACCOUNT_BALANCE

        file = open(filename, "a+")

        file.write(f"Step: {self.current_step}\n")
        file.write(f"Balance: {self.balance}\n")
        file.write(f"Shares held: {self.shares_held} (Total sold: {self.total_shares_sold})\n")
        file.write(f"Avg cost for held shares: {self.cost_basis} (Total sales value: {self.total_sales_value})\n")
        file.write(f"Net worth: {self.net_worth} (Max net worth: {self.max_net_worth})\n")
        file.write(f"Profit: {profit}\n\n")

        file.close()

    def step(self, action):
        # Execute one time step within the environment
        self._take_action(action)
        self.current_step += 1
        if self.current_step > len(self.df.loc[:, "Open"].values) - 6:
            self.current_step = 0
        delay_modifier = self.current_step / EnvConsts.MAX_STEPS

        # TODO: I want to optimize the number of shares since my objective is to accumulate more coins
        reward = self.balance * delay_modifier
        done = self.net_worth <= 0
        obs = self._next_observation()
        return obs, reward, done, {}

    def reset(self):
        """
        Reset the state of the environment to an initial state
        """
        self.balance = EnvConsts.INITIAL_ACCOUNT_BALANCE
        self.net_worth = EnvConsts.INITIAL_ACCOUNT_BALANCE
        self.max_net_worth = EnvConsts.INITIAL_ACCOUNT_BALANCE
        self.shares_held = 0
        self.cost_basis = 0
        self.total_shares_sold = 0
        self.total_sales_value = 0
        self.trades = []

        # Set the current step to a random point within the data frame
        self.current_step = random.randint(0, len(self.df.loc[:, "Open"].values) - 6)

        return self._next_observation()

    def render(self, mode="live", **kwargs):
        # Render the environment to the screen
        if mode == "file":
            self._render_to_file(kwargs.get("filename", "render.txt"))

        elif mode == "live":
            if self.visualization is None:
                self.visualization = StockTradingGraph(self.df, kwargs.get("title", None))

            if self.current_step > EnvConsts.LOOKBACK_WINDOW_SIZE:
                self.visualization.render(
                    self.current_step, self.net_worth, self.trades, window_size=EnvConsts.LOOKBACK_WINDOW_SIZE
                )
