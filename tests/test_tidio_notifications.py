import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import Base, TidioAlert
from app.tidio_service import check_unassigned_chats, format_alert
from app.notifications.tidio_telegram import TidioTelegramSendResult


class TidioNotificationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.engine = create_engine(f"sqlite:///{Path(self.tmp.name) / 'test.db'}", connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)
        self.session_patcher = patch("app.models.SessionLocal", self.SessionLocal)
        self.session_patcher.start()
        self.tidio_enabled = patch.object(settings, "tidio_enabled", True)
        self.telegram_enabled = patch.object(settings, "tidio_telegram_enabled", True)
        self.tidio_enabled.start()
        self.telegram_enabled.start()

    async def asyncTearDown(self):
        self.telegram_enabled.stop()
        self.tidio_enabled.stop()
        self.session_patcher.stop()
        self.engine.dispose()
        self.tmp.cleanup()

    async def test_new_thread_is_sent_and_deduplicated(self):
        thread = {
            "thread_id": "thread-123",
            "conversation_id": "conv-123",
            "visitor_id": "visitor-123",
            "thread_started_at": "2026-10-08T10:00:00Z",
            "thread_first_message_id": "message-1",
            "thread_intent": "billing",
            "initial_message_channel": "livechat",
        }
        sender = AsyncMock(return_value=TidioTelegramSendResult(True, True))
        with patch("app.tidio_service.get_unassigned_threads", new=AsyncMock(return_value=[thread])), \
             patch("app.tidio_service.send_tidio_telegram", new=sender):
            first = await check_unassigned_chats()
            second = await check_unassigned_chats()

        self.assertEqual(first["notified"], 1)
        self.assertEqual(second["notified"], 0)
        self.assertEqual(second["skipped"], 1)
        sender.assert_awaited_once()

        with self.SessionLocal() as db:
            row = db.query(TidioAlert).filter(TidioAlert.thread_id == "thread-123").one()
            self.assertEqual(row.conversation_id, "conv-123")

    async def test_failed_delivery_is_retryable(self):
        thread = {"thread_id": "thread-456"}
        sender = AsyncMock(return_value=TidioTelegramSendResult(False, False, "delivery failed"))
        with patch("app.tidio_service.get_unassigned_threads", new=AsyncMock(return_value=[thread])), \
             patch("app.tidio_service.send_tidio_telegram", new=sender):
            result = await check_unassigned_chats()

        self.assertEqual(result["notified"], 0)
        self.assertEqual(len(result["errors"]), 1)
        with self.SessionLocal() as db:
            self.assertIsNone(db.query(TidioAlert).filter(TidioAlert.thread_id == "thread-456").one_or_none())

    async def test_assignment_removal_and_reentry_sends_a_new_alert(self):
        thread = {"thread_id": "thread-789"}
        sender = AsyncMock(return_value=TidioTelegramSendResult(True, True))
        snapshots = [[thread], [], [thread]]

        async def get_threads():
            return snapshots.pop(0)

        with patch("app.tidio_service.get_unassigned_threads", new=get_threads), \
             patch("app.tidio_service.send_tidio_telegram", new=sender):
            appeared = await check_unassigned_chats()
            assigned = await check_unassigned_chats()
            unassigned_again = await check_unassigned_chats()

        self.assertEqual(appeared["notified"], 1)
        self.assertEqual(assigned["unassigned"], 0)
        self.assertEqual(unassigned_again["notified"], 1)
        self.assertEqual(sender.await_count, 2)

    def test_message_is_html_escaped(self):
        message = format_alert({"thread_id": "<script>", "thread_intent": "<x>"})
        self.assertNotIn("<script>", message)
        self.assertIn("&lt;script&gt;", message)
        self.assertIn("&lt;x&gt;", message)

    async def test_tidio_telegram_sender_uses_sales_chat_not_support_tech(self):
        from app.notifications import tidio_telegram

        class Response:
            def raise_for_status(self):
                pass

            def json(self):
                return {"ok": True}

        client = AsyncMock()
        client.post = AsyncMock(return_value=Response())
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=False)
        with patch.object(settings, "telegram_bot_token", "shared-token"), \
             patch.object(settings, "telegram_chat_id", "support-tech"), \
             patch.object(settings, "tidio_telegram_chat_id", "support-sales"), \
             patch("app.notifications.tidio_telegram.httpx.AsyncClient", return_value=client):
            result = await tidio_telegram.send("sales alert")

        self.assertTrue(result.success)
        self.assertEqual(client.post.await_args.kwargs["data"]["chat_id"], "support-sales")

    async def test_tidio_poll_uses_api_credentials_and_lookback_filters_unassigned_live_threads(self):
        from app import tidio_service

        class Response:
            def raise_for_status(self):
                pass

            def json(self):
                return [
                    {"thread_id": "new", "initial_message_channel": "livechat"},
                    {"thread_id": "answered", "thread_first_response_agent_id": 7},
                    {"thread_id": "ended", "thread_ended_at": "2026-10-09T10:00:00Z"},
                ]

        class Client:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args):
                return False

            async def get(self, *_args, **kwargs):
                self.kwargs = kwargs
                return Response()

        client = Client()
        with patch.object(settings, "tidio_client_id", "ci_example"), \
             patch.object(settings, "tidio_client_secret", "cs_private"), \
             patch.object(settings, "tidio_lookback_minutes", 20), \
             patch("app.tidio_service.httpx.AsyncClient", return_value=client):
            threads = await tidio_service.get_unassigned_threads()

        self.assertEqual([thread["thread_id"] for thread in threads], ["new"])
        self.assertEqual(client.kwargs["headers"]["X-Tidio-Openapi-Client-Id"], "ci_example")
        self.assertEqual(client.kwargs["headers"]["X-Tidio-Openapi-Client-Secret"], "cs_private")
        self.assertTrue(client.kwargs["params"]["thread_started_at"].startswith("gte."))

    async def test_tidio_api_errors_are_safe(self):
        with patch("app.tidio_service.get_unassigned_threads", new=AsyncMock(side_effect=RuntimeError("Tidio API returned HTTP 503"))), \
             patch.object(settings, "tidio_enabled", True):
            result = await check_unassigned_chats()
        self.assertEqual(result["errors"], ["Tidio API returned HTTP 503"])

    async def test_sales_monitor_starts_once_and_shutdown_cleans_up(self):
        from app.tidio_service import TidioService

        service = TidioService()
        with patch.object(settings, "tidio_enabled", True), \
             patch.object(settings, "tidio_poll_interval_seconds", 10), \
             patch("app.tidio_service.check_unassigned_chats", new=AsyncMock(return_value={
                 "unassigned": 0, "notified": 0, "skipped": 0, "errors": [],
             })):
            await service.start()
            task = service._task
            await service.start()
            self.assertIs(service._task, task)
            await service.shutdown()

        self.assertFalse(service.running)

    async def test_sales_test_endpoint_requires_admin_and_uses_sales_sender(self):
        from fastapi.testclient import TestClient
        from app import main
        from app.auth import Principal
        principal = Principal(id=1, username="admin", role="admin")

        sender = AsyncMock(return_value=TidioTelegramSendResult(True, True))
        with patch.object(settings, "tidio_telegram_enabled", True), \
             patch("app.main.send_tidio_telegram_test", new=sender), \
             patch("app.main.init_db"), patch("app.main.start_scheduler"), \
             patch("app.main.stop_scheduler"), \
             patch("app.main.tidio_monitor.restore", new=AsyncMock()), \
             patch("app.main.tidio_service.start", new=AsyncMock()), \
             patch("app.main.tidio_service.shutdown", new=AsyncMock()):
            with TestClient(main.app) as client:
                denied = client.post("/api/v1/notifications/test/tidio-telegram")
                self.assertEqual(denied.status_code, 401)
                main.app.dependency_overrides[main.require_admin] = lambda: principal
                try:
                    response = client.post("/api/v1/notifications/test/tidio-telegram")
                finally:
                    main.app.dependency_overrides.pop(main.require_admin, None)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        sender.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
