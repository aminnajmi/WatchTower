import tempfile
import unittest
from pathlib import Path

from app.config import Settings
from app.models import ensure_sqlite_directory


class ProductionConfigTests(unittest.TestCase):
    def _valid_production_settings(self, **overrides):
        values = {
            "_env_file": None,
            "app_env": "production",
            "jwt_secret": "a" * 64,
            "admin_username": "admin",
            "admin_password_hash": "ab" * 32,
            "admin_password_salt": "cd" * 16,
            "allowed_hosts": "tracker.example.com",
        }
        values.update(overrides)
        return Settings(**values)

    def test_production_configuration_accepts_secure_values(self):
        self._valid_production_settings().validate_production_settings()

    def test_production_configuration_rejects_missing_secrets_and_wildcard_host(self):
        config = self._valid_production_settings(jwt_secret="", allowed_hosts="*")
        with self.assertRaisesRegex(RuntimeError, "JWT_SECRET.*ALLOWED_HOSTS"):
            config.validate_production_settings()

    def test_production_configuration_requires_enabled_telegram_credentials(self):
        config = self._valid_production_settings(telegram_enabled=True)
        with self.assertRaisesRegex(RuntimeError, "TELEGRAM_BOT_TOKEN.*TELEGRAM_CHAT_ID"):
            config.validate_production_settings()

    def test_production_configuration_requires_separate_tidio_credentials_and_sales_chat(self):
        config = self._valid_production_settings(tidio_enabled=True, tidio_telegram_enabled=True)
        with self.assertRaisesRegex(RuntimeError, "TIDIO_CLIENT_ID.*TIDIO_CLIENT_SECRET.*TIDIO_TELEGRAM_CHAT_ID"):
            config.validate_production_settings()

        config = self._valid_production_settings(
            tidio_enabled=True,
            tidio_client_id="ci_test",
            tidio_client_secret="cs_test",
            tidio_telegram_enabled=True,
            tidio_telegram_chat_id="sales-chat",
            telegram_bot_token="shared-bot-token",
        )
        config.validate_production_settings()

    def test_sqlite_directory_is_created_for_nested_database_path(self):
        with tempfile.TemporaryDirectory() as root:
            database = Path(root) / "persistent" / "nested" / "tracker.db"
            ensure_sqlite_directory(f"sqlite:///{database}")
            self.assertTrue(database.parent.is_dir())


if __name__ == "__main__":
    unittest.main()
