from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "sqlite:///./os_tracker.db"
    request_timeout_seconds: float = 20
    allowed_hosts: str = "*"

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
    # Separate Telegram destination for Tidio unassigned/missed-chat alerts.
    tidio_enabled: bool = False
    tidio_telegram_enabled: bool = False
    tidio_telegram_chat_id: str = ""
    tidio_client_id: str = ""
    tidio_client_secret: str = ""
    # Browser fallback for accounts without Developer/OpenAPI access.
    tidio_web_email: str = ""
    tidio_web_password: str = ""
    tidio_web_headless: bool = True
    tidio_web_timeout_seconds: int = 20
    tidio_web_unassigned_label: str = "Unassigned"
    tidio_poll_interval_seconds: int = 10
    tidio_lookback_minutes: int = 60
    track_point_releases: bool = True
    openclaw_notification_api_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def validate_production_settings(self) -> None:
        """Fail startup on missing/unsafe credentials in production mode."""
        if self.app_env.strip().lower() not in {"production", "prod"}:
            return

        missing = []
        if len(self.jwt_secret) < 32:
            missing.append("JWT_SECRET must contain at least 32 characters")
        if not self.admin_username.strip():
            missing.append("ADMIN_USERNAME is required")
        if not self.admin_password_hash or not self.admin_password_salt:
            missing.append("ADMIN_PASSWORD_HASH and ADMIN_PASSWORD_SALT are required")
        else:
            try:
                bytes.fromhex(self.admin_password_hash)
                bytes.fromhex(self.admin_password_salt)
            except ValueError:
                missing.append("admin password hash and salt must be hexadecimal")
        hosts = [host.strip() for host in self.allowed_hosts.split(",") if host.strip()]
        if not hosts or "*" in hosts:
            missing.append("ALLOWED_HOSTS must list the deployed hostnames")
        if self.telegram_enabled:
            if not self.telegram_bot_token:
                missing.append("TELEGRAM_BOT_TOKEN is required when Telegram is enabled")
            if not self.telegram_chat_id:
                missing.append("TELEGRAM_CHAT_ID is required when Telegram is enabled")
        if self.tidio_telegram_enabled:
            if not self.telegram_bot_token:
                missing.append("TELEGRAM_BOT_TOKEN is required when TIDIO_TELEGRAM_ENABLED is true")
            if not self.tidio_telegram_chat_id:
                missing.append("TIDIO_TELEGRAM_CHAT_ID is required when TIDIO_TELEGRAM_ENABLED is true")
        # Tidio can be authenticated once from the administrator Settings page.
        # Therefore TIDIO_ENABLED does not require API credentials or a password
        # in the environment. If API credentials are configured they are used;
        # otherwise the persisted browser session is used.

        if missing:
            raise RuntimeError("Invalid production configuration: " + "; ".join(missing))


settings = Settings()
