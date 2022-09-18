from dynaconf import Dynaconf, Validator

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
        Validator("ticks_per_episode", is_type_of=int),
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
