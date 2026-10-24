
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    APP_NAME: str = "My API Service"
    # 下面的配置值仅用于本地开发环境，生产环境请通过环境变量覆盖。
    MYSQL_HOST: str = "192.168.1.36"
    MYSQL_PORT: int = 3307
    MYSQL_DATABASE: str = "luckde_app_users_db"
    MYSQL_USER: str = "futurelucky_test"
    MYSQL_PASSWORD: str = "SaUTgimQCssWnV85XIp3mbDqbrx1dbnj"
    # 生产环境请通过环境变量覆盖，避免凭证泄露。
    REDIS_HOST: str = "192.168.1.36"
    REDIS_PORT: int = 6380
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None
    # 生产环境请通过环境变量覆盖，避免凭证泄露。
    TOKEN_TTL_SECONDS: int = 24*60*60  # 24 小时

    # 第三方登录凭证：留空即关闭对应登录入口。
    # 这两个值来自 Apple / Google 开发者后台，属于环境相关配置，不应写进代码仓库；
    # 之前声明为必填项，导致没有 .env 的部署环境在启动阶段直接 ValidationError。
    APPLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_ID: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @staticmethod
    def _configured(value: str | None) -> bool:
        return bool(value and value.strip())

    @property
    def apple_login_enabled(self) -> bool:
        """APPLE_CLIENT_ID 已配置时，Apple 登录入口才可用。"""
        return self._configured(self.APPLE_CLIENT_ID)

    @property
    def google_login_enabled(self) -> bool:
        """GOOGLE_CLIENT_ID 已配置时，Google 登录入口才可用。"""
        return self._configured(self.GOOGLE_CLIENT_ID)


settings = Settings()
