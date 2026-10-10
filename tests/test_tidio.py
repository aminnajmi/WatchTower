import asyncio
from datetime import datetime
from unittest.mock import AsyncMock

from app.tidio import TidioMonitor, TidioSnapshot


def test_tidio_snapshot_defaults():
    snapshot = TidioSnapshot(False, "not_configured")
    assert snapshot.connected is False
    assert snapshot.unassigned_count == 0


def test_tidio_password_encryption_round_trip():
    monitor = TidioMonitor()
    encrypted = monitor.encrypt_password("example-password")
    assert encrypted != "example-password"
    assert monitor.decrypt_password(encrypted) == "example-password"


def test_tidio_session_is_encrypted_and_persisted(tmp_path, monkeypatch):
    monitor = TidioMonitor()
    session_path = tmp_path / "tidio-session.enc"
    monkeypatch.setenv("TIDIO_SESSION_PATH", str(session_path))

    class Context:
        async def storage_state(self):
            return {"cookies": [{"name": "session", "value": "secret-cookie"}], "origins": []}

    monitor._context = Context()
    asyncio.run(monitor._save_session())

    stored = session_path.read_bytes()
    assert b"secret-cookie" not in stored
    assert b'"cookies"' not in stored
    assert monitor._fernet().decrypt(stored).find(b"secret-cookie") >= 0
    assert session_path.stat().st_mode & 0o777 == 0o600


def test_tidio_verification_error_surfaces_authentication_required(monkeypatch):
    monitor = TidioMonitor()

    async def fail_login(*_args):
        raise RuntimeError("Tidio requires additional browser verification")

    async def noop(*_args):
        return None

    monkeypatch.setattr(monitor, "_close_browser", noop)
    monkeypatch.setattr(monitor, "_ensure_browser", noop)
    monkeypatch.setattr(monitor, "_login", fail_login)
    monkeypatch.setattr(monitor, "_save_credentials", noop)
    monkeypatch.setattr(monitor, "_set_enabled", noop)

    snapshot = asyncio.run(monitor.connect("admin@example.com", "password"))
    assert snapshot.connected is False
    assert snapshot.status == "authentication_required"
    assert snapshot.error.startswith("Authentication Required:")


def test_tidio_keeps_browser_open_for_manual_verification(monkeypatch):
    monitor = TidioMonitor()

    class Page:
        @staticmethod
        def is_closed():
            return False

    async def fail_login(*_args):
        raise RuntimeError("Tidio requires additional browser verification")

    async def noop(*_args):
        return None

    close_browser = AsyncMock()
    monitor._page = Page()
    monkeypatch.setattr(monitor, "_close_browser", close_browser)
    monkeypatch.setattr(monitor, "_ensure_browser", noop)
    monkeypatch.setattr(monitor, "_login", fail_login)
    monkeypatch.setattr(monitor, "_save_credentials", noop)
    monkeypatch.setattr(monitor, "_set_enabled", noop)

    snapshot = asyncio.run(monitor.connect("admin@example.com", "password"))
    assert snapshot.status == "authentication_required"
    assert monitor.authentication_interaction_available
    assert close_browser.await_count == 1  # Startup cleanup only; keep challenge browser open.
