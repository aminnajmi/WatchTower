from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./os_tracker.db"
    request_timeout_seconds: float = 20

    # Legacy machine-to-machine API key. Keep this for scripts/integrations.
    api_key: str = ""

    # JWT authentication for users/Swagger.
    jwt_secret: str = ""
    access_token_expire_minutes: int = 60
    admin_username: str = "admin"
    admin_password_hash: str = ""
    admin_password_salt: str = ""

    discord_webhook_url: str = ""
    telegram_enabled: bool = False
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    track_point_releases: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
