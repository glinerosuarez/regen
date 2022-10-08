from pathlib import Path

import pendulum
from cached_property import cached_property
from dynaconf import Dynaconf
from stable_baselines3.common.vec_env import VecEnv

import conf
from env import build_crypto_trading_env
from repository import TradingPair
from repository.db import DataBaseManager, Execution, TrainSettings
from repository.remote import BinanceClient
from vm._obs_producer import ObsProducer, KlineProducer
from vm.crypto_vm import CryptoViewModel


class DependencyInjector:
    
    @cached_property
    def settings(self) -> Dynaconf:
        return conf.load_settings()
    
    @property
    def output_dir(self) -> Path:
        return Path(self.settings.output_dir)

    @property
    def time_steps(self) -> int:
        return self.settings.time_steps

    @property
    def trading_pair(self) -> TradingPair:
        return TradingPair(self.settings.base_asset, self.settings.quote_asset)

    @cached_property
    def db_manager(self) -> DataBaseManager:
        return DataBaseManager(
            self.settings.db_name,
            DataBaseManager.EngineType.PostgreSQL
            if self.settings.db_type == "postgres"
            else DataBaseManager.EngineType.SQLite,
            self.settings.db_host,
            self.settings.db_user,
            self.settings.db_password,
            Path(self.settings.db_file_location),
        )

    @property
    def api_client(self) -> BinanceClient:
        return BinanceClient(
            base_urls=self.settings.bnb_base_urls,
            client_key=self.settings.bnb_client_key,
            client_secret=self.settings.bnb_client_secret,
        )

    @property
    def kline_producer(self) -> KlineProducer:
        return KlineProducer(
            db_manager=self.db_manager,
            api_manager=self.api_client,
            trading_pair=self.trading_pair,
            enable_live_mode=self.settings.enable_live_mode,
            get_data_from_db=self.settings.get_data_from_db,
            max_api_klines=self.settings.max_api_klines,
            klines_buffer_size=self.settings.klines_buffer_size,
        )

    @property
    def obs_producer(self) -> ObsProducer:
        return ObsProducer(kline_producer=self.kline_producer, window_size=self.settings.window_size)

    @cached_property
    def execution(self):
        return Execution(
            pair=self.trading_pair,
            algorithm=conf.consts.Algorithm.PPO,
            n_steps=self.settings.time_steps,
            start=pendulum.now("UTC").timestamp(),
            settings=TrainSettings(
                db_name=self.settings.db_name,
                window_size=self.settings.window_size,
                ticks_per_episode=self.settings.ticks_per_episode,
                is_live_mode=self.settings.enable_live_mode,
                klines_buffer_size=self.settings.klines_buffer_size,
            ),
        )

    @cached_property
    def exec_id(self):
        self.db_manager.insert(self.execution)
        return str(self.execution.id)

    @property
    def vm(self) -> CryptoViewModel:
        return CryptoViewModel(  # VM to get data from sources.
            trading_pair=self.trading_pair,
            db_manager=self.db_manager,
            api_client=self.api_client,
            obs_producer=self.obs_producer,
            ticks_per_episode=self.settings.ticks_per_episode,
            execution_id=self.exec_id,
            window_size=self.settings.window_size,
        )

    @property
    def env(self) -> VecEnv:
        return build_crypto_trading_env(vm=self.vm)


injector = DependencyInjector()
