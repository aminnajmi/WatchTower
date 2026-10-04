import asyncio
import logging
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app import main, notifications, service
from app import auth
from app.auth import Principal, create_access_token
from app.config import settings
from app.models import Base, OSRelease, ReleaseEvent, ReleaseHistory
from app.notifications.telegram import TelegramSendResult
from app.providers.base import Release


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {"ok": True, "result": {}}

    def raise_for_status(self):
        if self.status_code >= 400:
            import httpx
            request = httpx.Request("POST", "https://api.telegram.org/bot[redacted]/sendMessage")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError("request failed", request=request, response=response)

    def json(self):
        return self._payload


class FakeAsyncClient:
    def __init__(self, response):
        self.response = response
        self.post = AsyncMock(return_value=response)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False


class TelegramClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_disabled_does_not_make_request(self):
        from app.notifications import telegram
        with patch.object(settings, "telegram_enabled", False), \
             patch.object(telegram.httpx, "AsyncClient") as client:
            result = await telegram.send("test")
        self.assertTrue(result.success)
        self.assertFalse(result.sent)
        client.assert_not_called()

    async def test_missing_token_or_chat_id_returns_configuration_error(self):
        from app.notifications import telegram
        with patch.object(settings, "telegram_enabled", True), \
             patch.object(settings, "telegram_bot_token", ""), \
             patch.object(settings, "telegram_chat_id", "1701643905"):
            missing_token = await telegram.send("test")
        self.assertFalse(missing_token.success)
        self.assertIn("TELEGRAM_BOT_TOKEN", missing_token.error)

        with patch.object(settings, "telegram_enabled", True), \
             patch.object(settings, "telegram_bot_token", "test-secret"), \
             patch.object(settings, "telegram_chat_id", ""):
            missing_chat = await telegram.send("test")
        self.assertFalse(missing_chat.success)
        self.assertIn("TELEGRAM_CHAT_ID", missing_chat.error)

    async def test_success_uses_configured_chat_and_expected_message(self):
        from app.notifications import telegram
        client = FakeAsyncClient(FakeResponse())
        message = "🚨 New Major OS Release\n\nOS: Fedora\nNew Version: 45"
        with patch.object(settings, "telegram_enabled", True), \
             patch.object(settings, "telegram_bot_token", "test-secret"), \
             patch.object(settings, "telegram_chat_id", "1701643905"), \
             patch.object(telegram.httpx, "AsyncClient", return_value=client):
            result = await telegram.send(message)

        self.assertTrue(result.success)
        self.assertTrue(result.sent)
        url = client.post.await_args.args[0]
        self.assertEqual(url, "https://api.telegram.org/bottest-secret/sendMessage")
        self.assertEqual(client.post.await_args.kwargs["data"], {"chat_id": "1701643905", "text": message})

    async def test_api_failure_is_safe_and_logged_by_notifier(self):
        from app.notifications import telegram
        from app.notifications import notify
        client = FakeAsyncClient(FakeResponse(status_code=500))
        with patch.object(settings, "telegram_enabled", True), \
             patch.object(settings, "telegram_bot_token", "never-log-this-token"), \
             patch.object(settings, "telegram_chat_id", "1701643905"), \
             patch.object(telegram.httpx, "AsyncClient", return_value=client), \
             patch.object(notifications, "send_discord", new=AsyncMock()), \
             self.assertLogs("app.notifications.telegram", level=logging.WARNING) as captured:
            result = await notify("test")

        self.assertFalse(result[0])
        self.assertEqual(result[1], "Telegram API returned HTTP 500")
        self.assertIn("Telegram notification failed", "\n".join(captured.output))
        self.assertNotIn("never-log-this-token", "\n".join(captured.output))

    async def test_service_only_notifies_once_for_new_major_release(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = create_engine(f"sqlite:///{Path(directory) / 'telegram.db'}")
            Base.metadata.create_all(engine)
            sessions = sessionmaker(bind=engine, autoflush=False, autocommit=False)
            with sessions() as db:
                ubuntu = OSRelease(
                    slug="ubuntu", name="Ubuntu", version="26.04.1", major_version="26",
                    source_url="https://example.invalid", release_type="minor", is_rolling=False,
                )
                db.add(ubuntu)
                db.flush()
                db.add(ReleaseHistory(
                    os_id=ubuntu.id, version="26.04.1", major_version="26", release_type="minor",
                    source_url="https://example.invalid",
                ))
                db.commit()

            class UbuntuProvider:
                async def latest(self):
                    return Release("ubuntu", "Ubuntu", "28.04", None, "https://example.invalid")

            sender = AsyncMock(return_value=TelegramSendResult(success=True, sent=True))
            with patch.object(service, "SessionLocal", sessions), \
                 patch.object(service, "PROVIDERS", {"ubuntu": UbuntuProvider()}), \
                 patch.object(service, "send_telegram", new=AsyncMock()), \
                 patch("app.notifications.send_discord", new=AsyncMock()), \
                 patch("app.notifications.send_telegram", new=sender), \
                 patch.object(settings, "telegram_enabled", True):
                first = await service.check_all()
                second = await service.check_all()

            self.assertEqual(first["failed"], 0)
            self.assertEqual(first["major_releases"], 1)
            self.assertEqual(second["major_releases"], 0)
            sender.assert_awaited_once()
            sent_text = sender.await_args.args[0]
            self.assertIn("OS: Ubuntu", sent_text)
            self.assertIn("Previous Version: 26.04.1", sent_text)
            self.assertIn("New Version: 28.04", sent_text)
            self.assertIn("Major Version: 28", sent_text)

            with sessions() as db:
                events = db.scalars(select(ReleaseEvent)).all()
                self.assertEqual(len(events), 1)
                self.assertTrue(events[0].notification_sent)
                self.assertEqual(db.scalar(select(ReleaseHistory.version).where(ReleaseHistory.version == "28.04")), "28.04")
            engine.dispose()

    async def test_baseline_minor_arch_and_telegram_failure_do_not_fail_check(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = create_engine(f"sqlite:///{Path(directory) / 'telegram-edge.db'}")
            Base.metadata.create_all(engine)
            sessions = sessionmaker(bind=engine, autoflush=False, autocommit=False)
            versions = {"ubuntu": "26.04.1", "archlinux": "2026.10.01"}

            class FakeProvider:
                def __init__(self, slug):
                    self.slug = slug

                async def latest(self):
                    value = versions[self.slug]
                    return Release(self.slug, self.slug, value, None, "https://example.invalid", is_rolling=self.slug == "archlinux")

            sender = AsyncMock(return_value=TelegramSendResult(success=True, sent=True))
            with patch.object(service, "SessionLocal", sessions), \
             patch.object(service, "PROVIDERS", {slug: FakeProvider(slug) for slug in versions}), \
                 patch.object(service, "send_telegram", new=AsyncMock()), \
                 patch("app.notifications.send_discord", new=AsyncMock()), \
                 patch("app.notifications.send_telegram", new=sender):
                baseline = await service.check_all()
                versions["ubuntu"] = "26.04.2"
                versions["archlinux"] = "2026.11.01"
                minor_and_rolling = await service.check_all()

            self.assertEqual(baseline["failed"], 0)
            self.assertEqual(minor_and_rolling["failed"], 0)
            sender.assert_not_awaited()

            # A missing enabled credential is a notification error, while the
            # provider check still completes and does not increment provider failures.
            versions["ubuntu"] = "28.04"
            with patch.object(service, "SessionLocal", sessions), \
                 patch.object(service, "PROVIDERS", {"ubuntu": FakeProvider("ubuntu")}), \
                 patch.object(service, "send_telegram", new=AsyncMock()), \
                 patch("app.notifications.send_discord", new=AsyncMock()), \
                 patch.object(settings, "telegram_enabled", True), \
                 patch.object(settings, "telegram_bot_token", ""), \
                 patch.object(settings, "telegram_chat_id", "1701643905"), \
                 self.assertLogs("app.notifications", level=logging.WARNING):
                result = await service.check_all()
            self.assertEqual(result["checked"], 1)
            self.assertEqual(result["failed"], 0)
            self.assertEqual(len(result["notification_errors"]), 1)

            with patch.object(service, "SessionLocal", sessions), \
                 patch.object(service, "PROVIDERS", {"ubuntu": FakeProvider("ubuntu")}), \
                 patch.object(service, "send_telegram", new=AsyncMock()), \
                 patch("app.notifications.send_discord", new=AsyncMock()), \
                 patch.object(settings, "telegram_enabled", True), \
                 patch.object(settings, "telegram_bot_token", "test-token"), \
                 patch.object(settings, "telegram_chat_id", ""), \
                 self.assertLogs("app.notifications.telegram", level=logging.WARNING):
                missing_chat_result = await service.check_all()
            self.assertEqual(missing_chat_result["checked"], 1)
            self.assertEqual(missing_chat_result["failed"], 0)
            self.assertIn("TELEGRAM_CHAT_ID", missing_chat_result["notification_errors"][0]["error"])
            engine.dispose()

    async def test_every_completed_check_sends_one_telegram_summary_with_provider_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = create_engine(f"sqlite:///{Path(directory) / 'telegram-summary.db'}")
            Base.metadata.create_all(engine)
            sessions = sessionmaker(bind=engine, autoflush=False, autocommit=False)

            class HealthyProvider:
                async def latest(self):
                    return Release("ubuntu", "Ubuntu", "26.04.1", None, "https://example.invalid")

            class FailedProvider:
                async def latest(self):
                    raise RuntimeError("upstream unavailable")

            sender = AsyncMock(return_value=TelegramSendResult(success=True, sent=True))
            with patch.object(service, "SessionLocal", sessions), \
                 patch.object(service, "PROVIDERS", {"ubuntu": HealthyProvider(), "fedora": FailedProvider()}), \
                 patch.object(service, "notify", new=AsyncMock(return_value=(True, None))), \
                 patch.object(service, "send_telegram", new=sender), \
                 patch.object(settings, "telegram_enabled", True):
                result = await service.check_all()

            self.assertEqual((result["checked"], result["failed"]), (1, 1))
            sender.assert_awaited_once()
            message = sender.await_args.args[0]
            self.assertIn("⚠️ Check Completed", message)
            self.assertIn("1/2 providers healthy", message)
            self.assertIn("Fedora: provider unavailable", message)

            healthy_sender = AsyncMock(return_value=TelegramSendResult(success=True, sent=True))
            with patch.object(service, "SessionLocal", sessions), \
                 patch.object(service, "PROVIDERS", {"ubuntu": HealthyProvider()}), \
                 patch.object(service, "notify", new=AsyncMock(return_value=(True, None))), \
                 patch.object(service, "send_telegram", new=healthy_sender), \
                 patch.object(settings, "telegram_enabled", True):
                success = await service.check_all()
            self.assertEqual((success["checked"], success["failed"]), (1, 0))
            healthy_sender.assert_awaited_once()
            self.assertIn("✅ Check Completed", healthy_sender.await_args.args[0])
            self.assertIn("1/1 providers healthy", healthy_sender.await_args.args[0])

            failing_sender = AsyncMock(side_effect=RuntimeError("transport failure"))
            with patch.object(service, "SessionLocal", sessions), \
                 patch.object(service, "PROVIDERS", {"ubuntu": HealthyProvider()}), \
                 patch.object(service, "notify", new=AsyncMock(return_value=(True, None))), \
                 patch.object(service, "send_telegram", new=failing_sender), \
                 patch.object(settings, "telegram_enabled", True), \
                 self.assertLogs("app.service", level=logging.WARNING):
                telegram_failed = await service.check_all()
            self.assertEqual((telegram_failed["checked"], telegram_failed["failed"]), (1, 0))
            engine.dispose()


class TelegramTestEndpointTests(unittest.TestCase):
    def test_endpoint_requires_auth_and_sends_no_release_event(self):
        token = create_access_token(settings.admin_username)
        send_test = AsyncMock(return_value=TelegramSendResult(success=True, sent=True))
        with patch.object(main, "init_db"), patch.object(main, "start_scheduler"), \
             patch.object(main, "SessionLocal") as session_factory, \
             patch.object(auth, "principal_for_username", return_value=Principal(None, settings.admin_username, "admin")), \
             patch.object(main, "send_telegram_test", new=send_test), \
             patch.object(settings, "telegram_enabled", True), TestClient(main.app) as client:
            self.assertEqual(client.post("/api/v1/notifications/test/telegram").status_code, 401)
            response = client.post(
                "/api/v1/notifications/test/telegram",
                headers={"Authorization": f"Bearer {token}"},
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"success": True, "message": "Telegram test message sent"})
            send_test.assert_awaited_once()
            session_factory.assert_not_called()

    def test_endpoint_reports_disabled_and_does_not_send(self):
        send_test = AsyncMock()
        with patch.object(main, "init_db"), patch.object(main, "start_scheduler"), \
             patch.object(auth, "principal_for_username", return_value=Principal(None, settings.admin_username, "admin")), \
             patch.object(main, "send_telegram_test", new=send_test), \
             patch.object(settings, "telegram_enabled", False), TestClient(main.app) as client:
            token = create_access_token(settings.admin_username)
            response = client.post(
                "/api/v1/notifications/test/telegram",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])
        send_test.assert_not_awaited()

    def test_endpoint_handles_unexpected_sender_failure_without_exposing_details(self):
        send_test = AsyncMock(side_effect=RuntimeError("secret bot token in URL"))
        with patch.object(main, "init_db"), patch.object(main, "start_scheduler"), \
             patch.object(auth, "principal_for_username", return_value=Principal(None, settings.admin_username, "admin")), \
             patch.object(main, "send_telegram_test", new=send_test), \
             patch.object(settings, "telegram_enabled", True), TestClient(main.app) as client:
            token = create_access_token(settings.admin_username)
            response = client.post(
                "/api/v1/notifications/test/telegram",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("secret bot token", response.text)
        self.assertEqual(response.json()["error"], "Telegram test failed (RuntimeError)")

    def test_test_message_is_visibly_marked_as_test(self):
        from app.notifications import telegram
        sender = AsyncMock(return_value=TelegramSendResult(success=True, sent=True))
        with patch.object(telegram, "send", new=sender):
            result = asyncio.run(telegram.send_test())
        self.assertTrue(result.success)
        self.assertIn("TEST", sender.await_args.args[0])


if __name__ == "__main__":
    unittest.main()
