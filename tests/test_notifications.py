import asyncio
import logging
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import sessionmaker

from app import main, models, notification_service
from app.auth import create_access_token, generate_password_hash
from app.config import settings
from app.models import Base, Notification, OSRelease, User
from app.notification_middleware import NotificationBodyLimitMiddleware


class NotificationCenterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.engine = create_engine(f"sqlite:///{Path(self.temp.name) / 'notifications.db'}")
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)
        admin_hash, admin_salt = generate_password_hash("admin-password-for-test")
        user_hash, user_salt = generate_password_hash("normal-user-password-test")
        with self.sessions.begin() as db:
            db.add_all([
                User(username="admin", password_hash=f"pbkdf2_sha256$310000${admin_salt}${admin_hash}", role="admin"),
                User(username="reader", password_hash=f"pbkdf2_sha256$310000${user_salt}${user_hash}", role="user"),
            ])
        self.patches = [
            patch.object(main, "SessionLocal", self.sessions),
            patch.object(notification_service, "SessionLocal", self.sessions),
            patch.object(main, "init_db"),
            patch.object(main, "start_scheduler"),
            patch.object(settings, "jwt_secret", "notification-center-test-jwt-secret-0123456789"),
            patch.object(settings, "openclaw_notification_api_key", "openclaw-notification-test-key-0123456789"),
        ]
        for item in self.patches:
            item.start()
        self.addCleanup(self._stop_patches)
        self.admin_headers = {"Authorization": f"Bearer {create_access_token('admin')}"}
        self.user_headers = {"Authorization": f"Bearer {create_access_token('reader')}"}
        self.client = TestClient(main.app)
        self.client.__enter__()
        self.addCleanup(self._close_client)

    def _close_client(self):
        self.client.__exit__(None, None, None)
        self.engine.dispose()

    def _stop_patches(self):
        for item in reversed(self.patches):
            item.stop()

    def payload(self, **changes):
        data = {
            "source": "openclaw",
            "title": "Daily infrastructure check",
            "message": "The scheduled check completed.",
            "status": "new",
            "severity": "success",
            "task_name": "Daily infrastructure check",
            "metadata": {"servers_checked": 18, "healthy": 17, "issues": 1},
        }
        data.update(changes)
        return data

    def test_public_page_and_read_apis_need_no_user_session(self):
        page = self.client.get("/notifications")
        self.assertEqual(page.status_code, 200)
        self.assertIn("Notification Center", page.text)
        self.assertIn("Public read-only feed", page.text)
        self.assertNotIn("Signed in as", page.text)
        self.assertEqual(self.client.get("/api/v1/notifications").status_code, 200)

        created = self.client.post(
            "/api/v1/notifications",
            json=self.payload(),
            headers={"Authorization": f"Bearer {settings.openclaw_notification_api_key}"},
        )
        self.assertEqual(created.status_code, 201)
        detail = self.client.get(f"/api/v1/notifications/{created.json()['id']}")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["source"], "openclaw")

    def test_openclaw_key_is_required_and_never_logged_or_returned(self):
        key = settings.openclaw_notification_api_key
        with self.assertLogs("app.main", level=logging.INFO) as captured:
            missing = self.client.post("/api/v1/notifications", json=self.payload())
            invalid = self.client.post(
                "/api/v1/notifications", json=self.payload(),
                headers={"Authorization": "Bearer invalid-openclaw-key"},
            )
        self.assertEqual(missing.status_code, 401)
        self.assertEqual(invalid.status_code, 401)
        self.assertNotIn(key, "\n".join(captured.output))
        self.assertNotIn(key, missing.text + invalid.text)

    def test_missing_server_key_fails_closed(self):
        with patch.object(settings, "openclaw_notification_api_key", ""):
            response = self.client.post(
                "/api/v1/notifications", json=self.payload(),
                headers={"Authorization": "Bearer any-value"},
            )
        self.assertEqual(response.status_code, 503)

    def test_notification_storage_metadata_and_safe_external_link(self):
        response = self.client.post(
            "/api/v1/notifications", json=self.payload(external_url="https://reports.example.test/weekly"),
            headers={"Authorization": f"Bearer {settings.openclaw_notification_api_key}"},
        )
        self.assertEqual(response.status_code, 201)
        item = self.client.get(f"/api/v1/notifications/{response.json()['id']}").json()
        self.assertEqual(item["metadata"]["servers_checked"], 18)
        self.assertEqual(item["task_name"], "Daily infrastructure check")
        self.assertEqual(item["external_url"], "https://reports.example.test/weekly")
        self.assertEqual(item["status"], "new")
        self.assertNotIn("openclaw_notification_api_key", str(item))
        self.assertNotIn("reviewed_by", item)

    def test_html_like_content_and_unknown_metadata_are_rendered_as_text(self):
        created = self.client.post(
            "/api/v1/notifications",
            json=self.payload(
                title="<img src=x onerror=alert(1)>",
                metadata={"<b>custom</b>": "<svg onload=alert(1)>"},
            ),
            headers={"Authorization": f"Bearer {settings.openclaw_notification_api_key}"},
        )
        self.assertEqual(created.status_code, 201)
        detail = self.client.get(f"/api/v1/notifications/{created.json()['id']}").json()
        self.assertEqual(detail["title"], "<img src=x onerror=alert(1)>")
        self.assertEqual(detail["metadata"]["<b>custom</b>"], "<svg onload=alert(1)>")
        script = Path("static/js/notifications-center.js").read_text(encoding="utf-8")
        self.assertIn("node.textContent = text", script)
        self.assertNotIn("innerHTML", script)

    def test_notification_assets_are_served_by_existing_static_mount(self):
        self.assertEqual(self.client.get("/static/css/notifications.css").status_code, 200)
        self.assertEqual(self.client.get("/static/js/notifications-center.js").status_code, 200)
        self.assertEqual(self.client.get("/static/js/notifications.js").status_code, 200)

    def test_startup_adds_notification_table_without_replacing_existing_records(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "existing-watchtower.db"
            engine = create_engine(f"sqlite:///{path}")
            existing_tables = [table for table in Base.metadata.sorted_tables if table.name != "notifications"]
            Base.metadata.create_all(engine, tables=existing_tables)
            old_sessions = sessionmaker(bind=engine, autoflush=False, autocommit=False)
            with old_sessions.begin() as db:
                db.add(OSRelease(
                    slug="ubuntu", name="Ubuntu", version="26.04", major_version="26",
                    source_url="https://example.test", release_type="stable", is_rolling=False,
                ))
                db.add(User(username="kept-user", password_hash="existing-hash", role="user"))
            with patch.object(models, "engine", engine), \
                 patch.object(models.settings, "database_url", f"sqlite:///{path}"), \
                 patch.object(models.settings, "admin_password_hash", ""), \
                 patch.object(models.settings, "admin_password_salt", ""):
                models.init_db()
            with old_sessions() as db:
                self.assertEqual(db.scalar(select(OSRelease.name)), "Ubuntu")
                self.assertEqual(db.scalar(select(User.username)), "kept-user")
            self.assertIn("notifications", set(inspect(engine).get_table_names()))
            engine.dispose()

    def test_invalid_secrets_urls_and_large_payload_are_rejected(self):
        headers = {"Authorization": f"Bearer {settings.openclaw_notification_api_key}"}
        unsafe_url = self.client.post(
            "/api/v1/notifications", json=self.payload(external_url="javascript:alert(1)"), headers=headers
        )
        secret_metadata = self.client.post(
            "/api/v1/notifications", json=self.payload(metadata={"api_key": "secret-value"}), headers=headers
        )
        secret_message = self.client.post(
            "/api/v1/notifications", json=self.payload(message="password=do-not-save"), headers=headers
        )
        too_large = self.client.post(
            "/api/v1/notifications", json=self.payload(message="x" * 66000), headers=headers
        )
        self.assertEqual(unsafe_url.status_code, 422)
        self.assertEqual(secret_metadata.status_code, 422)
        self.assertEqual(secret_message.status_code, 422)
        self.assertEqual(too_large.status_code, 413)

    def test_chunked_notification_body_is_limited(self):
        async def exercise():
            messages = iter([
                {"type": "http.request", "body": b"x" * 40000, "more_body": True},
                {"type": "http.request", "body": b"y" * 30000, "more_body": False},
            ])
            sent = []

            async def receive():
                return next(messages)

            async def send(message):
                sent.append(message)

            async def endpoint(_scope, inner_receive, inner_send):
                while (await inner_receive()).get("more_body", False):
                    pass
                await inner_send({"type": "http.response.start", "status": 200, "headers": []})

            middleware = NotificationBodyLimitMiddleware(endpoint, max_bytes=65536)
            await middleware(
                {"type": "http", "method": "POST", "path": "/api/v1/notifications", "headers": []},
                receive,
                send,
            )
            return sent

        sent = asyncio.run(exercise())
        self.assertEqual(sent[0]["status"], 413)

    def test_source_severity_status_filters_pagination_and_newest_first(self):
        base_headers = {"Authorization": f"Bearer {settings.openclaw_notification_api_key}"}
        ids = []
        for source, severity, status in [
            ("openclaw", "warning", "new"),
            ("human_agent", "critical", "reviewed"),
            ("watchtower", "info", "resolved"),
        ]:
            response = self.client.post(
                "/api/v1/notifications", json=self.payload(source=source, severity=severity, status=status), headers=base_headers
            )
            self.assertEqual(response.status_code, 201)
            ids.append(response.json()["id"])

        all_rows = self.client.get("/api/v1/notifications?limit=2&offset=0").json()
        self.assertEqual([row["id"] for row in all_rows["items"]], ids[::-1][:2])
        self.assertEqual(all_rows["total"], 3)
        next_page = self.client.get("/api/v1/notifications?limit=2&offset=2").json()
        self.assertEqual([row["id"] for row in next_page["items"]], ids[:1])
        self.assertEqual(self.client.get("/api/v1/notifications?source=human_agent").json()["total"], 1)
        self.assertEqual(self.client.get("/api/v1/notifications?severity=critical").json()["total"], 1)
        self.assertEqual(self.client.get("/api/v1/notifications?status=reviewed").json()["total"], 1)
        self.assertEqual(self.client.get("/api/v1/notifications?status=resolved").json()["total"], 1)

    def test_since_filter_supports_incremental_polling(self):
        headers = {"Authorization": f"Bearer {settings.openclaw_notification_api_key}"}
        first = self.client.post("/api/v1/notifications", json=self.payload(), headers=headers).json()
        second = self.client.post("/api/v1/notifications", json=self.payload(title="Second check"), headers=headers).json()
        updates = self.client.get("/api/v1/notifications", params={"since": first["created_at"]}).json()
        self.assertEqual({item["id"] for item in updates["items"]}, {first["id"], second["id"]})

    def test_admin_test_button_endpoint_creates_shared_notification(self):
        unauthenticated = self.client.post("/api/v1/notifications/test")
        normal_user = self.client.post("/api/v1/notifications/test", headers=self.user_headers)
        self.assertEqual(unauthenticated.status_code, 401)
        self.assertEqual(normal_user.status_code, 403)

        created = self.client.post("/api/v1/notifications/test", headers=self.admin_headers)
        self.assertEqual(created.status_code, 201)
        item = created.json()
        self.assertEqual(item["source"], "watchtower")
        self.assertEqual(item["status"], "new")
        self.assertEqual(item["severity"], "info")
        self.assertEqual(item["metadata"], {"test": True, "source": "management_panel"})
        with self.sessions() as db:
            persisted = db.scalar(select(Notification).where(Notification.id == item["id"]))
            self.assertIsNotNone(persisted)
        self.assertEqual(self.client.get("/api/v1/notifications").json()["items"][0]["id"], item["id"])

    def test_feed_uses_safe_text_rendering_and_incremental_polling(self):
        script = Path("static/js/notifications-center.js").read_text(encoding="utf-8")
        self.assertIn("setInterval(poll, 12000)", script)
        self.assertIn("query.set('since', newestSeen)", script)
        self.assertIn("textContent", script)
        self.assertNotIn("innerHTML", script)
        self.client.post("/web/session", json={"access_token": create_access_token("admin")})
        settings_page = self.client.get("/settings")
        self.assertEqual(settings_page.status_code, 200)
        self.assertIn("Send Test Notification", settings_page.text)
        self.assertIn("/static/js/notifications.js", settings_page.text)
        test_script = Path("static/js/notifications.js").read_text(encoding="utf-8")
        self.assertIn("button.disabled = true", test_script)
        self.assertIn("Sending…", test_script)
        self.assertIn("Test notification sent", test_script)
        self.assertIn("Failed to send test notification", test_script)


if __name__ == "__main__":
    unittest.main()
