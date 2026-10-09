import asyncio
from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from cryptography.fernet import Fernet

from app import main
from app.config import settings
from app.tidio import TidioMonitor, TidioSnapshot


def test_tidio_snapshot_defaults():
    snapshot = TidioSnapshot(False, "not_configured")
    assert snapshot.connected is False
    assert snapshot.unassigned_count == 0


def test_tidio_password_encryption_round_trip(monkeypatch):
    monkeypatch.setattr(settings, "tidio_encryption_key", Fernet.generate_key().decode())
    monitor = TidioMonitor()
    encrypted = monitor.encrypt_password("example-password")
    assert encrypted != "example-password"
    assert monitor.decrypt_password(encrypted) == "example-password"


def test_tidio_encryption_requires_dedicated_stable_key(monkeypatch):
    monkeypatch.setattr(settings, "tidio_encryption_key", "")
    monkeypatch.setattr(settings, "jwt_secret", "jwt-secret-must-not-be-used")
    with pytest.raises(RuntimeError, match="TIDIO_ENCRYPTION_KEY"):
        TidioMonitor().encrypt_password("example-password")

    key_one, key_two = Fernet.generate_key().decode(), Fernet.generate_key().decode()
    monkeypatch.setattr(settings, "tidio_encryption_key", key_one)
    encrypted = TidioMonitor().encrypt_password("example-password")
    monkeypatch.setattr(settings, "tidio_encryption_key", key_two)
    with pytest.raises(RuntimeError, match="cannot be decrypted"):
        TidioMonitor().decrypt_password(encrypted)


def test_tidio_connect_reports_connected_only_after_successful_check(monkeypatch):
    monkeypatch.setattr(settings, "tidio_encryption_key", Fernet.generate_key().decode())
    monitor = TidioMonitor()
    monkeypatch.setattr(monitor, "_ensure_browser", AsyncMock())
    monkeypatch.setattr(monitor, "_close_browser", AsyncMock())
    monkeypatch.setattr(monitor, "_login", AsyncMock())
    monkeypatch.setattr(monitor, "_save_credentials", AsyncMock())
    monkeypatch.setattr(monitor, "_set_enabled", AsyncMock())

    async def successful_check():
        monitor._snapshot = TidioSnapshot(True, "connected", 3, datetime(2026, 1, 2))

    monkeypatch.setattr(monitor, "_check_once", successful_check)

    async def run():
        result = await monitor.connect("operator", "secret")
        assert result.connected is True
        assert result.unassigned_count == 3
        await monitor.shutdown()

    asyncio.run(run())


def test_tidio_status_payload_is_safe_and_reports_monitor_state(monkeypatch):
    class Row:
        username = "operator@example.com"
        password_encrypted = "encrypted-password"
        status = "connected"
        last_checked_at = datetime(2026, 1, 2)
        last_error = None

    class DB:
        def get(self, *_args):
            return Row()

        def close(self):
            pass

    monkeypatch.setattr(main, "SessionLocal", DB)
    monkeypatch.setattr(main.tidio_monitor, "_snapshot", TidioSnapshot(True, "connected", 4, datetime(2026, 1, 2)))
    payload = main._tidio_status_payload()
    assert payload["connected"] is True
    assert payload["unassigned_chats"] == 4
    assert payload["last_checked_at"]
    assert payload["username"] == "operator@example.com"
    assert "password" not in str(payload).lower()
    assert "encrypted-password" not in str(payload)


def test_tidio_browser_startup_failure_is_logged_and_cleaned_up(monkeypatch, caplog):
    class Chromium:
        async def launch(self, **kwargs):
            assert kwargs == {"headless": True}
            raise RuntimeError("Target page, context or browser has been closed")

    class Playwright:
        chromium = Chromium()
        stopped = False

        async def stop(self):
            self.stopped = True

    monitor = TidioMonitor()
    playwright = Playwright()
    monitor._playwright = playwright

    with pytest.raises(RuntimeError, match="Target page"):
        asyncio.run(monitor._ensure_browser())

    assert playwright.stopped is True
    assert monitor._playwright is None
    assert "Tidio Chromium launch failed" in caplog.text
    assert "Target page, context or browser has been closed" in caplog.text
    assert "Check server logs" in monitor._public_error(RuntimeError("Target page, context or browser has been closed"))


def test_tidio_disconnect_disables_monitoring_and_removes_saved_credentials(monkeypatch):
    class Row:
        username = "operator"
        password_encrypted = "ciphertext"
        enabled = True
        status = "connected"
        last_error = "old error"
        last_checked_at = datetime(2026, 1, 2)

    row = Row()

    class DB:
        def get(self, *_args):
            return row

        def commit(self):
            pass

        def close(self):
            pass

    monkeypatch.setattr("app.tidio.SessionLocal", DB)
    monitor = TidioMonitor()
    monkeypatch.setattr(monitor, "_close_browser", AsyncMock())
    asyncio.run(monitor.disconnect())
    assert row.username == ""
    assert row.password_encrypted == ""
    assert row.enabled is False
    assert row.status == "disconnected"
    assert monitor.snapshot.status == "disconnected"


def test_tidio_reconnect_uses_bounded_backoff(monkeypatch):
    monkeypatch.setattr(settings, "tidio_encryption_key", Fernet.generate_key().decode())
    now = [100.0]
    monkeypatch.setattr("app.tidio.time.monotonic", lambda: now[0])

    class Row:
        username = "operator"
        password_encrypted = TidioMonitor().encrypt_password("secret")
        enabled = True

    class DB:
        def get(self, *_args):
            return Row()

        def close(self):
            pass

    monkeypatch.setattr("app.tidio.SessionLocal", DB)
    monitor = TidioMonitor()
    monkeypatch.setattr(monitor, "_close_browser", AsyncMock())
    monkeypatch.setattr(monitor, "_ensure_browser", AsyncMock(side_effect=RuntimeError("browser failed")))
    monkeypatch.setattr(monitor, "_set_status", AsyncMock())

    async def run():
        await monitor._reconnect("Tidio session expired")
        assert monitor._reconnect_attempts == 1
        assert monitor._retry_at == 105.0
        now[0] = monitor._retry_at
        await monitor._reconnect("Tidio session expired")
        assert monitor._reconnect_attempts == 2
        assert monitor._retry_at == 120.0

    asyncio.run(run())


def test_tidio_mfa_stops_automatic_reconnect(monkeypatch):
    monkeypatch.setattr(settings, "tidio_encryption_key", Fernet.generate_key().decode())

    class Row:
        username = "operator"
        password_encrypted = TidioMonitor().encrypt_password("secret")
        enabled = True

    class DB:
        def get(self, *_args):
            return Row()

        def close(self):
            pass

    monkeypatch.setattr("app.tidio.SessionLocal", DB)
    monitor = TidioMonitor()
    monkeypatch.setattr(monitor, "_close_browser", AsyncMock())
    monkeypatch.setattr(monitor, "_ensure_browser", AsyncMock())
    monkeypatch.setattr(monitor, "_login", AsyncMock(side_effect=RuntimeError("Tidio requires additional browser verification")))
    set_enabled = AsyncMock()
    monkeypatch.setattr(monitor, "_set_enabled", set_enabled)
    monkeypatch.setattr(monitor, "_set_status", AsyncMock())

    asyncio.run(monitor._reconnect("Tidio session expired"))
    assert monitor.snapshot.status == "manual_verification_required"
    assert monitor._stop_event.is_set()
    set_enabled.assert_awaited_once_with(False)


def test_tidio_monitor_does_not_retry_before_backoff_deadline(monkeypatch):
    monitor = TidioMonitor()
    monitor._retry_at = 200.0
    monkeypatch.setattr("app.tidio.time.monotonic", lambda: 100.0)
    monkeypatch.setattr(monitor, "_check_once", AsyncMock(side_effect=RuntimeError("expired")))
    reconnect = AsyncMock()
    monkeypatch.setattr(monitor, "_reconnect", reconnect)

    async def wait_once(wait_coro, timeout):
        assert timeout == 3
        wait_coro.close()
        monitor._stop_event.set()

    monkeypatch.setattr("app.tidio.asyncio.wait_for", wait_once)
    asyncio.run(monitor._monitor_loop())
    reconnect.assert_not_awaited()
