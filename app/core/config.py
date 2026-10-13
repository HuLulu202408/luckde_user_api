
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    APP_NAME: str = "My API Service"
    MYSQL_HOST: str = "192.168.1.36"
    MYSQL_PORT: int = 3307
    MYSQL_DATABASE: str = "luckde_app_users_db"
    MYSQL_USER: str = "futurelucky_test"
    MYSQL_PASSWORD: str = "SaUTgimQCssWnV85XIp3mbDqbrx1dbnj"

    REDIS_HOST: str = "192.168.1.36"
    REDIS_PORT: int = 6380
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None

    TOKEN_TTL_SECONDS: int = 7200

    APPLE_CLIENT_ID: str
    GOOGLE_CLIENT_ID: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()