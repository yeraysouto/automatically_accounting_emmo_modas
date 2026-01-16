from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="EMMA_", extra="ignore")

    database_url: str = "sqlite:///./emma.db"


settings = Settings()
