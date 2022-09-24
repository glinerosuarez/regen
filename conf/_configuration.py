from pathlib import Path

from dynaconf import Dynaconf, Validator

from conf.consts import CryptoAsset

settings = Dynaconf(
    envvar_prefix="REGEN",
    settings_files=["settings.toml", ".secrets.toml"],
    environments=True,
    load_dotenv=True,
    env_switcher="REGEN_ENV",
    validators=[
        Validator("bnb_base_url", is_type_of=list),
        Validator("bnb_client_key", is_type_of=str),
        Validator("bnb_client_secret", is_type_of=str),
        Validator("app_name", is_type_of=str),
        Validator("db_name", is_type_of=str),
        Validator("base_asset", is_type_of=str, is_in=[CryptoAsset.__members__], default=CryptoAsset.BNB),
        Validator("quote_asset", is_type_of=str, is_in=[CryptoAsset.__members__], default=CryptoAsset.BUSD),
        Validator("window_size", is_type_of=int),
        Validator("ticks_per_episode", is_type_of=int),
        Validator("time_steps", is_type_of=int),
        Validator("output_dir", is_type_of=str),
        Validator("db_user", default=None),
        Validator("db_password", default=None),
        Validator("db_host", default=None),
        Validator("db_name", is_type_of=str),
        Validator("db_type", is_in=["sqlite", "postgres"]),
        Validator("enable_live_mode", is_type_of=bool, default=False),
        Validator("klines_buffer_size", is_type_of=int, default=10_000),
    ],
)


settings.validators.validate()

settings.output_dir = Path(settings.output_dir)

settings.base_asset = CryptoAsset(settings.base_asset)
settings.quote_asset = CryptoAsset(settings.quote_asset)