import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import main, models
from app.auth import SESSION_COOKIE_NAME, create_access_token, hash_user_password
from app.config import settings


class NotificationCenterTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "notifications.db"
        self.engine = create_engine(f"sqlite:///{self.db_path}", connect_args={"check_same_thread": False})
        models.Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)
        self.patches = [
            patch.object(main, "SessionLocal", self.sessions),
            patch.object(models, "engine", self.engine),
            patch.object(models, "SessionLocal", self.sessions),
            patch.object(main, "start_scheduler"),
            patch.object(main, "stop_scheduler"),
            patch.object(settings, "jwt_secret", "watchtower-notification-test-secret-32-chars-min"),
            patch.object(settings, "openclaw_notification_api_key", "openclaw-test-key"),
        ]
        for item in self.patches:
            item.start()
        with self.sessions.begin() as db:
            db.add_all([
                models.User(username="admin", password_hash=hash_user_password("admin-password"), role="admin", is_active=True),
                models.User(username="viewer", password_hash=hash_user_password("viewer-password"), role="user", is_active=True),
            ])
        self.client = TestClient(main.app)
        self.admin_headers = {"Authorization": f"Bearer {create_access_token('admin')}"}
        self.user_headers = {"Authorization": f"Bearer {create_access_token('viewer')}"}

    def tearDown(self):
        self.client.close()
        for item in reversed(self.patches):
            item.stop()
        self.engine.dispose()
        self.temp_dir.cleanup()

    def test_notification_center_requires_human_authentication(self):
        self.assertEqual(self.client.get("/notification-center", follow_redirects=False).status_code, 303)
        self.client.cookies.set(SESSION_COOKIE_NAME, create_access_token("viewer"))
        self.assertEqual(self.client.get("/notification-center").status_code, 200)
        response = self.client.get("/api/v1/notifications")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["items"], [])
        response = self.client.get("/api/v1/notifications", headers=self.user_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["items"], [])
        self.assertEqual(response.json()["unread_count"], 0)

    def test_only_admin_sees_notification_center_test_button(self):
        self.client.cookies.set(SESSION_COOKIE_NAME, create_access_token("viewer"))
        viewer_page = self.client.get("/notification-center")
        self.assertNotIn("Send Test Notification", viewer_page.text)
        self.client.cookies.set(SESSION_COOKIE_NAME, create_access_token("admin"))
        admin_page = self.client.get("/notification-center")
        self.assertIn('id="send-notification-test"', admin_page.text)
        self.assertIn("Send Test Notification", admin_page.text)

    def test_notification_center_has_mandatory_loud_alerts_without_mute_control(self):
        self.client.cookies.set(SESSION_COOKIE_NAME, create_access_token("viewer"))
        page = self.client.get("/notification-center")
        self.assertEqual(page.status_code, 200)
        self.assertIn("Loud alerts enabled", page.text)
        self.assertNotIn("Sound OFF", page.text)
        self.assertNotIn("notification-sound-toggle", page.text)
        script = Path("static/js/app.js").read_text()
        self.assertIn("playNotificationAlert()", script)
        self.assertNotIn("notificationSoundEnabled", script)
        self.assertIn("await loadNotifications({ silent: true })", script)
        self.assertIn("result.unread_count", script)
        self.assertNotIn("initializeNotificationTest", script)
        self.assertEqual(script.count("api('/api/v1/notifications/test'"), 1)

    def test_openclaw_ingestion_requires_api_key(self):
        payload = {"source": "openclaw", "title": "Task", "message": "Done", "severity": "success"}
        self.assertEqual(self.client.post("/api/v1/notifications", json=payload).status_code, 401)
        self.assertEqual(self.client.post("/api/v1/notifications", headers={"Authorization": "Bearer wrong"}, json=payload).status_code, 401)
        response = self.client.post("/api/v1/notifications", headers={"Authorization": "Bearer openclaw-test-key"}, json=payload)
        self.assertEqual(response.status_code, 201, response.text)
        item = response.json()
        self.assertEqual(item["source"], "openclaw")
        self.assertEqual(item["severity"], "success")
        self.assertNotIn("metadata_json", item)

    def test_admin_test_notification_uses_normal_feed_and_user_is_forbidden(self):
        self.assertEqual(self.client.post("/api/v1/notifications/test").status_code, 401)
        self.assertEqual(self.client.post("/api/v1/notifications/test", headers=self.user_headers).status_code, 403)
        from app.notifications import telegram
        with patch.object(telegram.httpx, "AsyncClient") as telegram_client:
            response = self.client.post("/api/v1/notifications/test", headers=self.admin_headers)
        telegram_client.assert_not_called()
        self.assertEqual(response.status_code, 201, response.text)
        item = response.json()
        self.assertEqual(item["source"], "system")
        self.assertEqual(item["title"], "Test Notification")
        self.assertEqual(item["message"], "WatchTower Notification Center is working correctly.")
        self.assertEqual(item["status"], "new")
        self.assertEqual(item["severity"], "info")
        self.assertTrue(item["metadata"]["test"])
        listed = self.client.get("/api/v1/notifications", headers=self.user_headers).json()
        self.assertEqual(listed["total"], 1)
        self.assertEqual(listed["unread_count"], 1)
        self.assertEqual(listed["items"][0]["id"], item["id"])
        refreshed = self.client.get("/api/v1/notifications", headers=self.user_headers).json()
        self.assertEqual(refreshed["items"][0]["id"], item["id"])

    def test_notification_filters_and_unsafe_external_url_are_rejected(self):
        headers = {"Authorization": "Bearer openclaw-test-key"}
        self.client.post("/api/v1/notifications", headers=headers, json={"source": "openclaw", "title": "A", "message": "A", "severity": "warning"})
        self.client.post("/api/v1/notifications", headers=headers, json={"source": "openclaw", "title": "B", "message": "B", "severity": "success"})
        response = self.client.get("/api/v1/notifications?severity=warning", headers=self.user_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["items"]), 1)
        unsafe = self.client.post("/api/v1/notifications", headers=headers, json={"source": "openclaw", "title": "X", "message": "X", "external_url": "javascript:alert(1)"})
        self.assertEqual(unsafe.status_code, 422)

    def test_openclaw_approval_request_can_be_approved_or_denied(self):
        payload = {
            "source": "openclaw",
            "title": "Approval Required",
            "message": "Create a change-location ticket for order 12345.",
            "severity": "warning",
            "requires_approval": True,
            "task_id": "task-12345",
            "task_name": "Create change location ticket",
            "metadata": {"order_id": "12345"},
        }
        response = self.client.post("/api/v1/notifications", headers={"Authorization": "Bearer openclaw-test-key"}, json=payload)
        self.assertEqual(response.status_code, 201, response.text)
        item = response.json()
        self.assertTrue(item["requires_approval"])
        self.assertEqual(item["approval_status"], "pending")

        response = self.client.post(f"/api/v1/notifications/{item['id']}/approve", headers=self.user_headers)
        self.assertEqual(response.status_code, 200, response.text)
        approved = response.json()
        self.assertEqual(approved["approval_status"], "approved")
        self.assertEqual(approved["status"], "resolved")
        self.assertEqual(approved["approved_by"], "viewer")

        response = self.client.post(f"/api/v1/notifications/{item['id']}/approve", headers=self.admin_headers)
        self.assertEqual(response.status_code, 409)

        response = self.client.get(f"/api/v1/notifications/{item['id']}", headers={"Authorization": "Bearer openclaw-test-key"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["approval_status"], "approved")

    def test_openclaw_approval_request_can_be_denied_with_reason(self):
        response = self.client.post(
            "/api/v1/notifications",
            headers={"Authorization": "Bearer openclaw-test-key"},
            json={"source": "openclaw", "title": "Approve task", "message": "Run task", "requires_approval": True},
        )
        item = response.json()
        response = self.client.post(
            f"/api/v1/notifications/{item['id']}/deny",
            headers=self.user_headers,
            json={"reason": "Not authorized for this order."},
        )
        self.assertEqual(response.status_code, 200, response.text)
        denied = response.json()
        self.assertEqual(denied["approval_status"], "denied")
        self.assertEqual(denied["denial_reason"], "Not authorized for this order.")



if __name__ == "__main__":
    unittest.main()
