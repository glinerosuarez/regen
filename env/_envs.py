import random
from enum import Enum
from typing import Optional, Union

import gym
import numpy as np
from gym import spaces
from gym.core import ObsType
from consts import EnvConsts, CryptoAsset
from env._render import StockTradingGraph
from vm.crypto_vm import CryptoViewModel


class CryptoTradingEnv(gym.Env):
    """Crypto asset trading environment that follows gym interface."""

    def __init__(self, window_size: int, base: CryptoAsset, quote: CryptoAsset):
        # Number of ticks (current and previous ticks) returned as an observation.
        self.window_size = window_size
        # Extracted features over time.
        self.signal_features = np.array([])
        # Shape of a single observation.
        self.shape = (window_size, self.signal_features.shape[1])
        # Actions of the format Buy x%, Sell x%, Hold, etc.
        self.action_space = spaces.Discrete(len(Action))
        # Prices contain the OHCL values for the last window_size prices.
        self.observation_space = spaces.Box(low=0, high=1, shape=self.shape, dtype=np.float32)
        # VM to get data from sources.
        self.vm = CryptoViewModel(base_asset=base, quote_asset=quote, window_size=window_size)

    def reset(self, *, seed: Optional[int] = None, return_info: bool = False, options: Optional[dict] = None) -> Union[
        ObsType, tuple[ObsType, dict]]:
        self.vm.reset()
        self._done = False
        self._current_tick = self._start_tick
        self._last_trade_tick = self._current_tick - 1

        self._position_history = (self.window_size * [None]) + [self._position]
        self._total_reward = 0.
        self._total_profit = 1.  # unit
        self._first_rendering = True
        self.history = {}
        return self.vm.get_observation()

    def step(self, action):
        self._done = False
        self._current_tick += 1

        # TODO: This is not applicable to our use case, here we should define the conditions to end the episode.
        #if self._current_tick == self._end_tick:
        #    self._done = True

        step_reward = self.vm.calculate_reward(action)
        self._total_reward += step_reward

        self._update_profit(action)

        trade = False
        if ((action == Actions.Buy.value and self._position == Positions.Short) or
                (action == Actions.Sell.value and self._position == Positions.Long)):
            trade = True

        if trade:
            self._position = self._position.opposite()
            self._last_trade_tick = self._current_tick

        self._position_history.append(self._position)
        observation = self._get_observation()
        info = dict(
            total_reward = self._total_reward,
            total_profit = self._total_profit,
            position = self._position.value
        )
        self._update_history(info)

        return observation, step_reward, self._done, info

'''
    def reset(self):
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

        return self._next_observation()'''






    def _process_data(self):
        raise NotImplementedError

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
