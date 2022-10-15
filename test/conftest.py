import random
from logging import Logger
from typing import List, Optional

import pytest
from dynaconf import Dynaconf
from stable_baselines3.common.vec_env import VecEnv

import log
from conf import load_settings
from conf.consts import CryptoAsset, Action
from env import build_crypto_trading_env
from repository import TradingPair
from repository.db import Kline, DataBaseManager
from repository.remote import BinanceClient
from vm._obs_producer import ObsProducer, KlineProducer
from vm.crypto_vm import CryptoViewModel


@pytest.fixture(autouse=True)
def settings() -> Dynaconf:
    return load_settings("development")


@pytest.fixture
def enable_live_mode() -> bool:
    return False


@pytest.fixture
def get_data_from_db() -> bool:
    return True


@pytest.fixture
def max_api_klines() -> Optional[bool]:
    return None


@pytest.fixture
def klines_buffer_size() -> int:
    return 10_000


@pytest.fixture(autouse=True, scope="session")
def set_random_seed() -> None:
    random.seed(24)


@pytest.fixture
def execution_id() -> str:
    return "24"


@pytest.fixture
def base() -> CryptoAsset:
    return CryptoAsset.BNB


@pytest.fixture
def quote() -> CryptoAsset:
    return CryptoAsset.BUSD


@pytest.fixture
def trading_pair(base: CryptoAsset, quote: CryptoAsset) -> TradingPair:
    return TradingPair(base=base, quote=quote)


@pytest.fixture
def ticks_per_episode() -> int:
    return 1_440


@pytest.fixture
def window_size() -> int:
    return 5


@pytest.fixture
def actions() -> List[Action]:
    return [
        Action.Sell,
        Action.Sell,
        Action.Sell,
        Action.Sell,
        Action.Buy,
        Action.Buy,
        Action.Sell,
        Action.Buy,
        Action.Buy,
        Action.Buy,
        Action.Buy,
        Action.Sell,
        Action.Sell,
        Action.Buy,
    ]


@pytest.fixture
def klines_data(trading_pair: TradingPair) -> List[Kline]:
    return [
        Kline(
            pair=trading_pair,
            open_time=1598843460000,
            open_value=23.5778,
            high=23.5902,
            low=23.5778,
            close_value=23.5901,
            volume=8.95,
            close_time=1598843519999,
            quote_asset_vol=211.072225,
            trades=6,
            taker_buy_base_vol=4.26,
            taker_buy_quote_vol=100.44552,
        ),
        Kline(
            pair=trading_pair,
            open_time=1598843520000,
            open_value=23.597,
            high=23.597,
            low=23.5865,
            close_value=23.5942,
            volume=54.92,
            close_time=1598843579999,
            quote_asset_vol=1295.449426,
            trades=10,
            taker_buy_base_vol=4.15,
            taker_buy_quote_vol=97.899483,
        ),
        Kline(
            pair=trading_pair,
            open_time=1598843580000,
            open_value=23.588,
            high=23.5952,
            low=23.588,
            close_value=23.5952,
            volume=4.11,
            close_time=1598843639999,
            quote_asset_vol=96.96252,
            trades=2,
            taker_buy_base_vol=1.91,
            taker_buy_quote_vol=45.05308,
        ),
        Kline(
            pair=trading_pair,
            open_time=1598843640000,
            open_value=23.59,
            high=23.59,
            low=23.5776,
            close_value=23.5889,
            volume=6.1,
            close_time=1598843699999,
            quote_asset_vol=143.874938,
            trades=3,
            taker_buy_base_vol=4.0,
            taker_buy_quote_vol=94.335938,
        ),
        Kline(
            pair=trading_pair,
            open_time=1598843700000,
            open_value=23.5724,
            high=23.5724,
            low=23.5569,
            close_value=23.5678,
            volume=32.6,
            close_time=1598843759999,
            quote_asset_vol=768.143046,
            trades=11,
            taker_buy_base_vol=6.17,
            taker_buy_quote_vol=145.387863,
        ),
        Kline(
            pair=trading_pair,
            open_time=1598843760000,
            open_value=23.5751,
            high=23.5751,
            low=23.5661,
            close_value=23.5661,
            volume=8.46,
            close_time=1598843819999,
            quote_asset_vol=199.404748,
            trades=3,
            taker_buy_base_vol=6.37,
            taker_buy_quote_vol=150.137387,
        ),
        Kline(
            pair=trading_pair,
            open_time=1598843820000,
            open_value=23.5625,
            high=23.5625,
            low=23.5591,
            close_value=23.5591,
            volume=8.01,
            close_time=1598843879999,
            quote_asset_vol=188.729459,
            trades=4,
            taker_buy_base_vol=6.11,
            taker_buy_quote_vol=143.961469,
        ),
        Kline(
            pair=trading_pair,
            open_time=1598843880000,
            open_value=23.5635,
            high=23.5635,
            low=23.5635,
            close_value=23.5635,
            volume=1.35,
            close_time=1598843939999,
            quote_asset_vol=31.810725,
            trades=1,
            taker_buy_base_vol=0.0,
            taker_buy_quote_vol=0.0,
        ),
        Kline(
            pair=trading_pair,
            open_time=1598843940000,
            open_value=23.5561,
            high=23.5561,
            low=23.5073,
            close_value=23.5308,
            volume=285.51,
            close_time=1598843999999,
            quote_asset_vol=6720.007968,
            trades=41,
            taker_buy_base_vol=1.25,
            taker_buy_quote_vol=29.413553,
        ),
        Kline(
            pair=trading_pair,
            open_time=1598844000000,
            open_value=23.5285,
            high=23.5326,
            low=23.5285,
            close_value=23.5326,
            volume=3.35,
            close_time=1598844059999,
            quote_asset_vol=78.82724,
            trades=2,
            taker_buy_base_vol=3.35,
            taker_buy_quote_vol=78.82724,
        ),
        Kline(
            pair=trading_pair,
            open_time=1598844060000,
            open_value=23.55,
            high=23.5532,
            low=23.5473,
            close_value=23.5473,
            volume=12.15,
            close_time=1598844119999,
            quote_asset_vol=286.150046,
            trades=6,
            taker_buy_base_vol=2.5,
            taker_buy_quote_vol=58.875,
        ),
        Kline(
            pair=trading_pair,
            open_time=1598844120000,
            open_value=23.531,
            high=23.5336,
            low=23.515,
            close_value=23.515,
            volume=74.35,
            close_time=1598844179999,
            quote_asset_vol=1749.298269,
            trades=21,
            taker_buy_base_vol=23.0,
            taker_buy_quote_vol=541.225696,
        ),
        Kline(
            pair=trading_pair,
            open_time=1598844180000,
            open_value=23.5126,
            high=23.5291,
            low=23.5126,
            close_value=23.518,
            volume=11.53,
            close_time=1598844239999,
            quote_asset_vol=271.17873,
            trades=5,
            taker_buy_base_vol=9.65,
            taker_buy_quote_vol=226.96489,
        ),
        Kline(
            pair=trading_pair,
            open_time=1598844240000,
            open_value=23.5213,
            high=23.5213,
            low=23.5213,
            close_value=23.5213,
            volume=1.97,
            close_time=1598844299999,
            quote_asset_vol=46.336961,
            trades=1,
            taker_buy_base_vol=0.0,
            taker_buy_quote_vol=0.0,
        ),
        Kline(
            pair=trading_pair,
            open_time=1598844300000,
            open_value=23.5213,
            high=23.5213,
            low=23.5213,
            close_value=23.5213,
            volume=0.0,
            close_time=1598844359999,
            quote_asset_vol=0.0,
            trades=0,
            taker_buy_base_vol=0.0,
            taker_buy_quote_vol=0.0,
        ),
        Kline(
            pair=trading_pair,
            open_time=1598844360000,
            open_value=23.5102,
            high=23.5297,
            low=23.5102,
            close_value=23.5297,
            volume=18.74,
            close_time=1598844419999,
            quote_asset_vol=440.851466,
            trades=5,
            taker_buy_base_vol=18.74,
            taker_buy_quote_vol=440.851466,
        ),
        Kline(
            pair=trading_pair,
            open_time=1598844420000,
            open_value=23.5338,
            high=23.5603,
            low=23.5338,
            close_value=23.5594,
            volume=38.41,
            close_time=1598844479999,
            quote_asset_vol=904.790747,
            trades=12,
            taker_buy_base_vol=14.42,
            taker_buy_quote_vol=339.689271,
        ),
        Kline(
            pair=trading_pair,
            open_time=1598844480000,
            open_value=23.5594,
            high=23.5594,
            low=23.5594,
            close_value=23.5594,
            volume=0.0,
            close_time=1598844539999,
            quote_asset_vol=0.0,
            trades=0,
            taker_buy_base_vol=0.0,
            taker_buy_quote_vol=0.0,
        ),
        Kline(
            pair=trading_pair,
            open_time=1598844540000,
            open_value=23.5597,
            high=23.5597,
            low=23.5357,
            close_value=23.545,
            volume=47.42,
            close_time=1598844599999,
            quote_asset_vol=1116.725358,
            trades=10,
            taker_buy_base_vol=11.39,
            taker_buy_quote_vol=268.104807,
        ),
        Kline(
            pair=trading_pair,
            open_time=1598844600000,
            open_value=23.5448,
            high=23.5567,
            low=23.5448,
            close_value=23.5483,
            volume=9.07,
            close_time=1598844659999,
            quote_asset_vol=213.598461,
            trades=5,
            taker_buy_base_vol=4.0,
            taker_buy_quote_vol=94.215808,
        ),
    ]


@pytest.fixture
def logger() -> Logger:
    return log.LoggerFactory.get_console_logger(__name__)


@pytest.fixture
def db_name() -> str:
    return "test_db"


@pytest.fixture
def db_manager(db_name, tmp_path) -> DataBaseManager:
    return DataBaseManager(db_name, files_dir=tmp_path)


@pytest.fixture
def api_client(settings, db_manager, logger) -> BinanceClient:
    return BinanceClient(
        base_urls=["https://testnet.binance.vision"],
        client_key=settings.bnb_client_key,
        client_secret=settings.bnb_client_secret,
        db_manager=db_manager,
        logger=logger,
    )


@pytest.fixture
def kline_producer(
    db_manager, api_client, trading_pair, enable_live_mode, get_data_from_db, max_api_klines, klines_buffer_size, logger
) -> KlineProducer:
    return KlineProducer(
        db_manager=db_manager,
        api_manager=api_client,
        trading_pair=trading_pair,
        enable_live_mode=enable_live_mode,
        get_data_from_db=get_data_from_db,
        max_api_klines=max_api_klines,
        klines_buffer_size=klines_buffer_size,
        logger=logger,
    )


@pytest.fixture
def obs_producer(kline_producer, window_size, logger) -> ObsProducer:
    return ObsProducer(kline_producer=kline_producer, window_size=window_size, logger=logger)


@pytest.fixture
def vm(
    trading_pair, db_manager, api_client, obs_producer, ticks_per_episode, execution_id, window_size
) -> CryptoViewModel:
    return CryptoViewModel(
        trading_pair=trading_pair,
        db_manager=db_manager,
        api_client=api_client,
        obs_producer=obs_producer,
        ticks_per_episode=ticks_per_episode,
        execution_id=execution_id,
        window_size=window_size,
    )


@pytest.fixture
def env(vm) -> VecEnv:
    return build_crypto_trading_env(vm=vm)


@pytest.fixture
def insert_klines(db_name, db_manager, klines_data) -> None:
    db_manager.insert(klines_data)
