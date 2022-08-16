import time
from typing import Optional
from collections import defaultdict
from functools import cached_property

import numpy as np

import log
import configuration
from consts import CryptoAsset, Side
from vm.consts import Action, Position
from vm._obs_producer import KlinesProducer
from repository.remote import BinanceClient
from repository.db import DataBaseManager, Kline
from repository import EnvState, Observation, TradingPair


class ObsProducer:
    _OBS_TYPE = "float32"

    def _get_obs_page_generator(self):
        offset = 0
        page = DataBaseManager.select(Observation, offset=offset, limit=self.page_size)
        while len(page) > 0:
            yield page
            offset += self.page_size
            page = DataBaseManager.select(Observation, offset=offset, limit=self.page_size)

    def _get_db_obs_generator(self):
        for page in self._get_obs_page_generator():
            for obs in page:
                yield obs

    def __init__(self, trading_pair: TradingPair, window_size: int, execution_id: int, use_db_buffer: bool = True):
        self.use_db_buffer = use_db_buffer  # Deliver observations from the database or not
        self.execution_id = execution_id
        self.logger = log.LoggerFactory.get_console_logger(__name__)

        self.producer = KlinesProducer(trading_pair, window_size)
        if not self.producer.is_alive():
            self.producer.start()

        self.page_size = 10_000
        self.db_buffer = self._get_db_obs_generator()
        self.next_observation = next(self.db_buffer, None)

    def get_observation(self, episode_id: int) -> tuple[np.ndarray, Optional[bool]]:
        """
        Deliver an observation either from the database or a new one from the api.
        :return: Observation data and a flag to identify the end of an episode.
        """

        def klines_to_numpy(klines: list[Kline]):
            # TODO: I saw an observation with a record whose volume was equal to 0 and then in the next observation that
            #  same tick has a different value for the volume
            return np.array(  # Return observation as a numpy array because everybody uses numpy.
                [np.array([kl.open_value, kl.high, kl.low, kl.close_value, kl.volume]) for kl in klines]
            ).astype(self._OBS_TYPE)

        if (obs := self.next_observation) is not None and self.use_db_buffer:
            self.logger.debug(f"Serving {obs=} from database.")
            self.next_observation = next(self.db_buffer, None)
            return (
                klines_to_numpy(obs.klines),
                (
                    # If there's no next obs then this is the last obs in the db and an episode end,
                    self.next_observation is None
                    or
                    # if the execution_id is different in the next obs then this is the last obs in this episode.
                    obs.execution_id != self.next_observation.execution_id
                    or
                    # if the episode_id is different in the next obs then this is the last obs in this episode.
                    obs.episode_id != self.next_observation.episode_id
                ),
            )
        else:
            while True:
                if self.producer.is_alive():
                    if self.producer.queue.empty():
                        time.sleep(self.producer.frequency / 2)
                        continue
                    else:
                        obs_data = self.producer.queue.get()
                        self.logger.debug(f"Getting {obs_data} : {self.producer.queue.qsize()} elements in queue.")
                        self.logger.debug("Saving observation in database.")
                        DataBaseManager.insert(
                            Observation(execution_id=self.execution_id, episode_id=episode_id, klines=obs_data)
                        )
                        return klines_to_numpy(obs_data), False


class CryptoViewModel:
    def __init__(
        self,
        base_asset: CryptoAsset,
        quote_asset: CryptoAsset,
        window_size: int,
        base_balance: float = 0,
        quote_balance: float = 0,
        trade_fee_ask_percent: float = 0.0,
        trade_fee_bid_percent: float = 0.0,
    ):
        """
        :param base_asset: The crypto asset we want to accumulate.
        :param quote_asset: The crypto asset we trade our main asset against.
        :param window_size: Number of ticks (current and previous ticks) returned as an observation.
        """
        if not base_balance and not quote_balance:
            raise ValueError("Both base_balance and quote_balance are equal to zero, you need assets to create the env")

        self.base_asset = base_asset
        self.quote_asset = quote_asset
        self.trading_pair = TradingPair(base_asset, quote_asset)
        # Number of ticks (current and previous ticks) returned as an observation.
        self.window_size = window_size
        self.base_balance = base_balance
        self.quote_balance = quote_balance
        # The ask price represents the minimum price that a seller is willing to take for that same security, so this is
        # the fee the exchange charges for buying.
        self.trade_fee_ask_percent = trade_fee_ask_percent
        # The bid price represents the maximum price that a buyer is willing to pay for a share of stock or other
        # security, so this is the fee the exchange charges for buying.
        self.trade_fee_bid_percent = trade_fee_bid_percent

        DataBaseManager.init_connection(configuration.settings.db_name)  # Create connection to database
        DataBaseManager.create_all()

        self.episode_id = None
        self.position = Position.Short
        self.start_tick = window_size
        self.current_tick = None
        self.total_reward = 0.0
        self.done = None
        self.position_history = (self.window_size * [None]) + [self.position]
        self.history = defaultdict(list)
        self.client = BinanceClient()
        self.last_observation = None
        self.last_price = None
        self.last_trade_price = None
        self.initial_price = None
        self.logger = log.LoggerFactory.get_console_logger(__name__)
        self.obs_producer = ObsProducer(self.trading_pair, self.window_size, self.execution_id)

    def reset(self):
        self.logger.debug("Resetting environment.")

        self.done = False
        self.current_tick = self.window_size

        # We always start longing
        # TODO: Remove the option that allows passing quote balance, since our purpose is always to accumulate the base
        #  asset
        if self.base_balance < self.quote_balance:
            self._place_order(Side.SELL)

        self.position = Position.Long
        self.position_history = (self.window_size * [None]) + [self.position]
        self.total_reward = 0.0
        self.last_price = None
        self.last_trade_price = None
        self.episode_id = 1 if self._get_last_episode_id() is None else self._get_last_episode_id() + 1
        self.logger.debug(f"Updating episode_id, new value: {self.episode_id}")

        # TODO: episodes should have a min num of steps i.e. it doesn't make sense to have an episode with only 2 steps
        self.last_observation, done = self.obs_producer.get_observation(self.episode_id)
        # The initial price is the last price in the first observation
        self.initial_price = self.last_observation[-1][3]
        # We normalize prices dividing by the initial price
        self.last_observation[:, :3] = self.last_observation[:, :3] / self.initial_price
        return dict(klines=self.last_observation, position=Position.Long.value)

    def step(self, action: Action):
        # TODO: Finish episode if balance goes to 0
        self.done = False

        step_reward = self._calculate_reward(action)
        self.total_reward += step_reward

        self.position_history.append(self.position)
        self.last_observation, self.done = self.obs_producer.get_observation(self.episode_id)
        info = dict(
            total_reward=self.total_reward,
            base_balance=self.base_balance,
            quote_balance=self.quote_balance,
            position=self.position.value,
        )
        self._update_history(info)

        # TODO: for now, an episode has a fixed length of _TICKS_PER_EPISODE ticks.
        self.current_tick += 1
        if self.current_tick >= configuration.settings.ticks_per_episode:
            self.done = True

        # We normalize prices dividing by the last trade price
        non_null_last_trade_price = self.last_trade_price if self.last_trade_price is not None else self.initial_price
        self.last_observation[:, :3] = self.last_observation[:, :3] / non_null_last_trade_price

        return (
            dict(klines=self.last_observation, position=self.position.value),
            step_reward,
            self.done,
            info,
        )

    @cached_property
    def execution_id(self) -> int:
        last_exec_id = DataBaseManager.select_max(EnvState.execution_id)
        return 1 if last_exec_id is None else last_exec_id + 1

    def _get_last_episode_id(self) -> Optional[int]:
        """Get the last episode id in this execution, return None if there's no last episode id."""
        return DataBaseManager.select_max(col=EnvState.episode_id, condition=EnvState.execution_id == self.execution_id)

    def _is_trade(self, action: Action):
        return any(
            [
                action == Action.Buy and self.position == Position.Short,
                action == Action.Sell and self.position == Position.Long,
            ]
        )

    def _calculate_reward(self, action: Action):
        # TODO: During training, the reward is computed based on the close price of the observation that the agent
        #  interacted with, in practice, this price will vary because of the succeeding market movements and the fact
        #  that we always buy at market price (for simplicity, we could change that in the future), this makes things
        #  easier for the agent, this difference will depend mainly on the time that elapses between the moment the
        #  agent takes a trade action and the moment the order is processed (measure that time on average), to start
        #  with, I think we could take a random value from (open, close) of the next observation (because we get a new
        #  observation every minute, frequently)
        step_reward = 0.0
        if self._is_trade(action):
            quantity, self.last_price = self._place_order(Side.BUY if action == Action.Buy else Side.SELL)

            if self.position == Position.Short:  # Our objective is to accumulate the base.
                # We normalize the rewards as percentages, this way, changes in price won't affect the agent's behavior
                step_reward = (self.last_trade_price - self.last_price) / self.last_trade_price

            self.last_trade_price = self.last_price  # Update last trade price

            self._store_env_state_data(action, is_trade=True)
            self._update_balances(action, quantity, self.last_price)

            self.position = self.position.opposite()
        else:
            self.last_price = self._get_price()
            self._store_env_state_data(action, is_trade=False)

        return step_reward

    def _store_env_state_data(self, action: Action, is_trade: bool) -> None:
        DataBaseManager.insert(
            EnvState(
                execution_id=self.execution_id,
                episode_id=self.episode_id,
                tick=self.current_tick,
                price=self.last_price,
                position=self.position,
                action=action,
                is_trade=is_trade,
                ts=time.time(),
            )
        )

    def _update_balances(self, action: Action, quantity: float, price: float) -> None:
        if self._is_trade(action) or self.done:
            if action == Action.Buy:
                self.base_balance = quantity
                self.quote_balance = 0.0
            else:
                self.base_balance = 0.0
                self.quote_balance = quantity * price

    def _update_history(self, info):
        for key, value in info.items():
            self.history[key].append(value)

    def _place_order(self, side: Side) -> tuple[float, float]:
        # order = self.client.place_order(
        #    pair=self.trading_pair,
        #    side=side,
        #    type=OrderType.MARKET,
        #    quantity=self.balance,
        #    new_client_order_id=self.execution_id
        # )
        # TODO: Get trade price.
        # TODO: Add a trade_fee_percent to make training harder for the agent
        price = self._get_price()
        # The price and quantity will be returned by client.place_order.
        if side == Side.BUY:
            quantity = self.quote_balance * (1 - self.trade_fee_bid_percent) / price
        else:
            quantity = self.base_balance * (1 - self.trade_fee_ask_percent)
        return quantity, price

    def _get_price(self):
        price = self.last_observation[-1][3]
        self.logger.debug(f"Returning {price=} for {self.last_observation=}")
        return price
