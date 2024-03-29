from pathlib import Path
from typing import Optional, Union

from dynaconf import Dynaconf, Validator
from conf.consts import CryptoAsset


def load_settings(
    env: Optional[str] = None,
    settings_path: Union[str, Path] = "settings.toml",
    secrets_path: Union[str, Path] = ".secrets.toml",
):
    settings = Dynaconf(
        envvar_prefix="REGEN",
        settings_files=[settings_path, secrets_path],
        environments=True,
        force_env=env,
        load_dotenv=True,
        env_switcher="REGEN_ENV",
        validators=[
            Validator("bnb_base_urls", is_type_of=list),
            Validator("bnb_client_key", is_type_of=str),
            Validator("bnb_client_secret", is_type_of=str),
            Validator("app_name", is_type_of=str),
            Validator("db_name", is_type_of=str),
            Validator("db_file_location", is_type_of=str, default="."),
            Validator("base_asset", is_type_of=str, is_in=CryptoAsset.__members__, default=CryptoAsset.BNB.value),
            Validator("quote_asset", is_type_of=str, is_in=CryptoAsset.__members__, default=CryptoAsset.BUSD.value),
            Validator("window_size", is_type_of=int, default=5),
            Validator("ticks_per_episode", is_type_of=int),
            Validator("time_steps", is_type_of=int),
            Validator("output_dir", is_type_of=str, default=str((Path() / "output").absolute())),
            Validator("DB_USER", default=None),
            Validator("DB_PASSWORD", default=None),
            Validator("DB_HOST", default=None),
            Validator("db_type", is_in=["sqlite", "postgres"]),
            Validator("enable_live_mode", is_type_of=bool, default=False),
            Validator("get_data_from_db", is_type_of=bool, default=True),
            Validator("max_api_klines", default=None),
            Validator("klines_buffer_size", is_type_of=int, default=10_000),
            Validator("path_to_env_stats", is_type_of=str, default="output/1/env/env.pkl"),
            Validator("load_from_execution_id", default=None),
            Validator("update_klines_db", is_type_of=bool, default=False),
            Validator("place_orders", is_type_of=bool, default=False),
            Validator("env_logging_lvl", is_type_of=str, default="INFO"),
            Validator("obs_table", is_type_of=str, default="observations"),
            Validator("db_schema", is_type_of=str),
        ],
    )

    settings.validators.validate()

    # Conversions
    settings.base_asset = CryptoAsset(settings.base_asset)
    settings.quote_asset = CryptoAsset(settings.quote_asset)

    return settings
