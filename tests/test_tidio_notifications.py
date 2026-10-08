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
            self.assertTrue(row.is_active)

    async def test_new_thread_increases_current_count_but_existing_thread_does_not_alert_again(self):
        thread1 = {"thread_id": "thread-1"}
        thread2 = {"thread_id": "thread-2"}
        sender = AsyncMock(return_value=TidioTelegramSendResult(True, True))
        with patch("app.tidio_service.get_unassigned_threads", new=AsyncMock(side_effect=[[thread1], [thread1], [thread1, thread2], [thread2]])), \
             patch("app.tidio_service.send_tidio_telegram", new=sender):
            first = await check_unassigned_chats()
            second = await check_unassigned_chats()
            third = await check_unassigned_chats()
            fourth = await check_unassigned_chats()

        self.assertEqual(first["current_unassigned"], 1)
        self.assertEqual(first["new_unassigned"], 1)
        self.assertEqual(first["notified"], 1)
        self.assertEqual(second["current_unassigned"], 1)
        self.assertEqual(second["new_unassigned"], 0)
        self.assertEqual(second["notified"], 0)
        self.assertEqual(third["current_unassigned"], 2)
        self.assertEqual(third["new_unassigned"], 1)
        self.assertEqual(third["notified"], 1)
        self.assertEqual(fourth["current_unassigned"], 1)
        self.assertEqual(fourth["new_unassigned"], 0)
        self.assertEqual(fourth["notified"], 0)
        self.assertEqual(fourth["removed"], 1)
        self.assertEqual(sender.await_count, 2)

    async def test_reassigned_thread_can_alert_again(self):
        thread = {"thread_id": "thread-requeue"}
        sender = AsyncMock(return_value=TidioTelegramSendResult(True, True))
        with patch("app.tidio_service.get_unassigned_threads", new=AsyncMock(side_effect=[[thread], [], [thread]])), \
             patch("app.tidio_service.send_tidio_telegram", new=sender):
            first = await check_unassigned_chats()
            second = await check_unassigned_chats()
            third = await check_unassigned_chats()

        self.assertEqual(first["notified"], 1)
        self.assertEqual(second["current_unassigned"], 0)
        self.assertEqual(second["removed"], 1)
        self.assertEqual(third["notified"], 1)
        self.assertEqual(sender.await_count, 2)

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

    def test_message_is_html_escaped(self):
        message = format_alert({"thread_id": "<script>", "thread_intent": "<x>"})
        self.assertNotIn("<script>", message)
        self.assertIn("&lt;script&gt;", message)
        self.assertIn("&lt;x&gt;", message)


if __name__ == "__main__":
    unittest.main()
