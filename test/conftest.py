import random
from logging import Logger
from typing import List, Optional

import pendulum
import pytest
from dynaconf import Dynaconf
from stable_baselines3.common.vec_env import VecEnv

import log
from conf import load_settings
from conf.consts import CryptoAsset, Action
from env import build_crypto_trading_env
from repository import TradingPair
from repository.db import Kline, DataBaseManager, ObsData
from repository.remote import BinanceClient
from vm._obs_producer import ObsProducer, ObsDataProducer
from vm.crypto_vm import CryptoViewModel


@pytest.fixture(autouse=True)
def settings() -> Dynaconf:
    return load_settings("development")


@pytest.fixture
def enable_live_mode() -> bool:
    return False


@pytest.fixture
def obs_table() -> str:
    return "observations"


@pytest.fixture
def obs_table_schema() -> str:
    return None


@pytest.fixture
def n_features() -> int:
    return 11


@pytest.fixture
def obs_buffer_size() -> int:
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
def obs_data(klines_data) -> List[ObsData]:
    return [
        ObsData(**data)
        for data in [
            {
                "kline_id": 1561,
                "open_value": 13.6036,
                "high": 13.6036,
                "low": 13.6036,
                "close_value": 13.6036,
                "ma_7": 13.96,
                "ma_25": 13.985972,
                "ma_100": 14.007432,
                "ma_300": 14.018822,
                "ma_1440": 13.769572,
                "ma_14400": 13.380736,
                "ma_144000": 16.958823,
                "open_ts": 1577577600000,
            },
            {
                "kline_id": 1562,
                "open_value": 13.6036,
                "high": 13.6036,
                "low": 13.6036,
                "close_value": 13.6036,
                "ma_7": 13.899286,
                "ma_25": 13.971072,
                "ma_100": 14.002193,
                "ma_300": 14.017527,
                "ma_1440": 13.769666,
                "ma_14400": 13.380762,
                "ma_144000": 16.958768,
                "open_ts": 1577577660000,
            },
            {
                "kline_id": 1563,
                "open_value": 13.6036,
                "high": 13.6036,
                "low": 13.6036,
                "close_value": 13.6036,
                "ma_7": 13.838571,
                "ma_25": 13.956172,
                "ma_100": 13.996954,
                "ma_300": 14.016232,
                "ma_1440": 13.769799,
                "ma_14400": 13.38079,
                "ma_144000": 16.958713,
                "open_ts": 1577577720000,
            },
            {
                "kline_id": 1564,
                "open_value": 13.6538,
                "high": 13.6538,
                "low": 13.6538,
                "close_value": 13.6538,
                "ma_7": 13.785029,
                "ma_25": 13.94328,
                "ma_100": 13.991932,
                "ma_300": 14.015104,
                "ma_1440": 13.769967,
                "ma_14400": 13.380821,
                "ma_144000": 16.958658,
                "open_ts": 1577577780000,
            },
            {
                "kline_id": 1565,
                "open_value": 13.6538,
                "high": 13.6538,
                "low": 13.6538,
                "close_value": 13.6538,
                "ma_7": 13.734114,
                "ma_25": 13.930388,
                "ma_100": 13.98691,
                "ma_300": 14.013976,
                "ma_1440": 13.770135,
                "ma_14400": 13.380853,
                "ma_144000": 16.958604,
                "open_ts": 1577577840000,
            },
            {
                "kline_id": 1566,
                "open_value": 13.6158,
                "high": 13.6158,
                "low": 13.6158,
                "close_value": 13.6158,
                "ma_7": 13.677771,
                "ma_25": 13.915976,
                "ma_100": 13.981304,
                "ma_300": 14.012721,
                "ma_1440": 13.770277,
                "ma_14400": 13.380882,
                "ma_144000": 16.95855,
                "open_ts": 1577577900000,
            },
            {
                "kline_id": 1567,
                "open_value": 13.6385,
                "high": 13.6385,
                "low": 13.6302,
                "close_value": 13.6302,
                "ma_7": 13.623486,
                "ma_25": 13.90214,
                "ma_100": 13.975842,
                "ma_300": 14.011514,
                "ma_1440": 13.770403,
                "ma_14400": 13.380911,
                "ma_144000": 16.958496,
                "open_ts": 1577577960000,
            },
            {
                "kline_id": 1568,
                "open_value": 13.6302,
                "high": 13.6302,
                "low": 13.6302,
                "close_value": 13.6302,
                "ma_7": 13.627286,
                "ma_25": 13.888304,
                "ma_100": 13.97038,
                "ma_300": 14.010174,
                "ma_1440": 13.770528,
                "ma_14400": 13.380939,
                "ma_144000": 16.958442,
                "open_ts": 1577578020000,
            },
            {
                "kline_id": 1569,
                "open_value": 13.6302,
                "high": 13.6302,
                "low": 13.6302,
                "close_value": 13.6302,
                "ma_7": 13.631086,
                "ma_25": 13.874152,
                "ma_100": 13.964918,
                "ma_300": 14.008786,
                "ma_1440": 13.770654,
                "ma_14400": 13.380966,
                "ma_144000": 16.958388,
                "open_ts": 1577578080000,
            },
            {
                "kline_id": 1570,
                "open_value": 13.6302,
                "high": 13.6302,
                "low": 13.6302,
                "close_value": 13.6302,
                "ma_7": 13.634886,
                "ma_25": 13.86,
                "ma_100": 13.960225,
                "ma_300": 14.007398,
                "ma_1440": 13.77078,
                "ma_14400": 13.380995,
                "ma_144000": 16.958334,
                "open_ts": 1577578140000,
            },
            {
                "kline_id": 1571,
                "open_value": 13.6302,
                "high": 13.6302,
                "low": 13.6302,
                "close_value": 13.6302,
                "ma_7": 13.631514,
                "ma_25": 13.845848,
                "ma_100": 13.955532,
                "ma_300": 14.00601,
                "ma_1440": 13.770905,
                "ma_14400": 13.381023,
                "ma_144000": 16.95828,
                "open_ts": 1577578200000,
            },
            {
                "kline_id": 1572,
                "open_value": 13.6302,
                "high": 13.6302,
                "low": 13.6302,
                "close_value": 13.6302,
                "ma_7": 13.628143,
                "ma_25": 13.831696,
                "ma_100": 13.951199,
                "ma_300": 14.004622,
                "ma_1440": 13.771031,
                "ma_14400": 13.381052,
                "ma_144000": 16.958225,
                "open_ts": 1577578260000,
            },
            {
                "kline_id": 1573,
                "open_value": 13.6302,
                "high": 13.6302,
                "low": 13.6302,
                "close_value": 13.6302,
                "ma_7": 13.6302,
                "ma_25": 13.816372,
                "ma_100": 13.947065,
                "ma_300": 14.003234,
                "ma_1440": 13.771137,
                "ma_14400": 13.381078,
                "ma_144000": 16.958171,
                "open_ts": 1577578320000,
            },
            {
                "kline_id": 1574,
                "open_value": 13.6354,
                "high": 13.6354,
                "low": 13.6074,
                "close_value": 13.6074,
                "ma_7": 13.626943,
                "ma_25": 13.800136,
                "ma_100": 13.942364,
                "ma_300": 14.00177,
                "ma_1440": 13.771252,
                "ma_14400": 13.381103,
                "ma_144000": 16.958117,
                "open_ts": 1577578380000,
            },
            {
                "kline_id": 1575,
                "open_value": 13.6074,
                "high": 13.6074,
                "low": 13.6074,
                "close_value": 13.6074,
                "ma_7": 13.623686,
                "ma_25": 13.7839,
                "ma_100": 13.937663,
                "ma_300": 14.000306,
                "ma_1440": 13.771366,
                "ma_14400": 13.381127,
                "ma_144000": 16.958063,
                "open_ts": 1577578440000,
            },
            {
                "kline_id": 1576,
                "open_value": 13.6074,
                "high": 13.6074,
                "low": 13.6074,
                "close_value": 13.6074,
                "ma_7": 13.620429,
                "ma_25": 13.767664,
                "ma_100": 13.932962,
                "ma_300": 13.998842,
                "ma_1440": 13.771481,
                "ma_14400": 13.381152,
                "ma_144000": 16.958008,
                "open_ts": 1577578500000,
            },
            {
                "kline_id": 1577,
                "open_value": 13.6074,
                "high": 13.6074,
                "low": 13.6074,
                "close_value": 13.6074,
                "ma_7": 13.617171,
                "ma_25": 13.749952,
                "ma_100": 13.928141,
                "ma_300": 13.997378,
                "ma_1440": 13.771596,
                "ma_14400": 13.381176,
                "ma_144000": 16.957954,
                "open_ts": 1577578560000,
            },
            {
                "kline_id": 1578,
                "open_value": 13.6074,
                "high": 13.6074,
                "low": 13.6074,
                "close_value": 13.6074,
                "ma_7": 13.613914,
                "ma_25": 13.733104,
                "ma_100": 13.92332,
                "ma_300": 13.996122,
                "ma_1440": 13.77171,
                "ma_14400": 13.381201,
                "ma_144000": 16.9579,
                "open_ts": 1577578620000,
            },
            {
                "kline_id": 1579,
                "open_value": 13.6354,
                "high": 13.6354,
                "low": 13.6354,
                "close_value": 13.6354,
                "ma_7": 13.614657,
                "ma_25": 13.717376,
                "ma_100": 13.919637,
                "ma_300": 13.99496,
                "ma_1440": 13.771844,
                "ma_14400": 13.381228,
                "ma_144000": 16.957846,
                "open_ts": 1577578680000,
            },
            {
                "kline_id": 1580,
                "open_value": 13.6354,
                "high": 13.6354,
                "low": 13.6354,
                "close_value": 13.6354,
                "ma_7": 13.6154,
                "ma_25": 13.701648,
                "ma_100": 13.915954,
                "ma_300": 13.993798,
                "ma_1440": 13.771978,
                "ma_14400": 13.381255,
                "ma_144000": 16.957792,
                "open_ts": 1577578740000,
            },
        ]
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
def obs_data_producer(
    db_manager, obs_table, obs_table_schema, enable_live_mode, obs_buffer_size, logger
) -> ObsDataProducer:
    return ObsDataProducer(
        db_manager=db_manager,
        table=obs_table,
        schema=obs_table_schema,
        enable_live_mode=enable_live_mode,
        buffer_size=obs_buffer_size,
        logger=logger,
    )


@pytest.fixture
def obs_producer(obs_data_producer, window_size, n_features, logger) -> ObsProducer:
    return ObsProducer(obs_data_prod=obs_data_producer, window_size=window_size, n_features=n_features, logger=logger)


@pytest.fixture
def vm(
    trading_pair, db_manager, api_client, obs_producer, ticks_per_episode, execution_id, window_size, logger
) -> CryptoViewModel:
    return CryptoViewModel(
        trading_pair=trading_pair,
        db_manager=db_manager,
        api_client=api_client,
        obs_producer=obs_producer,
        ticks_per_episode=ticks_per_episode,
        execution_id=execution_id,
        window_size=window_size,
        logger=logger,
    )


@pytest.fixture
def env(vm) -> VecEnv:
    return build_crypto_trading_env(vm=vm)


@pytest.fixture
def insert_klines(db_manager, klines_data) -> None:
    db_manager.insert(klines_data)


@pytest.fixture
def insert_obs(db_manager, obs_data) -> None:
    db_manager.insert_rows(table_name="observations", rows=[list(vars(od).values()) for od in obs_data])


@pytest.fixture
def create_obs_table(db_manager) -> None:
    db_manager.create_table("observations", {k: "TEXT" for k in ObsData.__dataclass_fields__.keys()})


@pytest.fixture
def insert_obs_2ep(db_manager, create_obs_table, obs_data) -> None:
    for i in range(10, 20):
        obs_data[i].open_ts = pendulum.from_timestamp(obs_data[i].open_ts / 1_000).add(minutes=1).timestamp() * 1_000
    # breakpoint()
    db_manager.insert_rows(table_name="observations", rows=[vars(od) for od in obs_data])


@pytest.fixture
def insert_klines_2ep(db_manager, klines_data) -> None:
    klines = []
    for i, kl in enumerate(klines_data):
        if i > 9:
            klines.append(
                kl.copy(
                    with_={
                        "open_time": pendulum.from_timestamp(kl.open_time / 1_000).add(minutes=1).timestamp() * 1_000,
                        "close_time": pendulum.from_timestamp(kl.close_time / 1_000).add(minutes=1).timestamp() * 1_000,
                    }
                )
            )
        else:
            klines.append(kl)
    db_manager.insert(klines)
