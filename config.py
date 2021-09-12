from dynaconf import Dynaconf, Validator

settings = Dynaconf(
    envvar_prefix="REGEN",
    settings_files=['settings.toml', '.secrets.toml'],
    environments=True,
    load_dotenv=True,
    env_switcher="REGEN_ENV",
    validators=[
        Validator("bnb_base_url", is_type_of=str),
        Validator("bnb_client_key", is_type_of=str),
        Validator("bnb_client_secret", is_type_of=str),
        Validator("app_name", is_type_of=str),
    ]
)

settings.validators.validate()
