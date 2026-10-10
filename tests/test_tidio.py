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


def test_tidio_waits_for_inbox_client_render():
    monitor = TidioMonitor()

    class Body:
        reads = 0

        async def inner_text(self, timeout):
            self.reads += 1
            return "Unassigned" if self.reads > 1 else "Tidio"

    class Page:
        url = "https://www.tidio.com/panel/inbox/operators/conversations/allOperators"

        def __init__(self):
            self.body = Body()

        @staticmethod
        def is_closed():
            return False

        def locator(self, _selector):
            return self.body

        @staticmethod
        async def wait_for_timeout(_timeout):
            await asyncio.sleep(0)

    monitor._page = Page()
    assert asyncio.run(monitor._wait_for_inbox_content(timeout_ms=1_000)) is True


def test_tidio_inbox_render_wait_is_bounded():
    monitor = TidioMonitor()

    class Body:
        @staticmethod
        async def inner_text(timeout):
            return "Tidio"

    class Page:
        url = "https://www.tidio.com/panel/inbox/operators/conversations/allOperators"

        @staticmethod
        def is_closed():
            return False

        @staticmethod
        def locator(_selector):
            return Body()

    monitor._page = Page()
    assert asyncio.run(monitor._wait_for_inbox_content(timeout_ms=0)) is False


def test_tidio_console_diagnostics_redact_error_text(caplog):
    class Message:
        type = "error"
        text = "Uncaught TypeError: secret-token-value was rejected"
        location = {"url": "https://code.tidio.co/app.js?token=secret", "lineNumber": 42}

    TidioMonitor._log_console_error(Message())

    assert "category=type_error" in caplog.text
    assert "host=code.tidio.co" in caplog.text
    assert "secret-token-value" not in caplog.text
    assert "token=secret" not in caplog.text
