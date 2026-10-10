import os
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect
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
        self.assertIn("notification-task-details", script)
        self.assertIn("Target website", script)
        self.assertIn("notification-target-link", script)
        render_function = script.split("function renderNotification(notification) {", 1)[1].split("\n  async function initializeNotificationCenter", 1)[0]
        for hidden_field in ("task_spec_sha256", "task_schema_version", "action_id", "created_by", "Task type", "task.version"):
            self.assertNotIn(hidden_field, render_function)
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

    def test_task_bound_approval_is_canonical_immutable_and_verifiable(self):
        headers = {"Authorization": "Bearer openclaw-test-key"}
        body = {
            "source": "openclaw", "title": "Inspect public site", "message": "Review pages",
            "requires_approval": True,
            "task_spec": {
                "version": 1, "task_type": "public_website_inspection",
                "url": "HTTPS://OperaVPS.com:443",
            },
        }
        created = self.client.post("/api/v1/notifications", headers=headers, json=body)
        self.assertEqual(created.status_code, 201, created.text)
        notification = created.json()
        expected_spec = {
            "version": 1, "task_type": "public_website_inspection",
            "url": "https://operavps.com/",
        }
        canonical = json.dumps(expected_spec, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        expected_digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        self.assertEqual(notification["task_specification"], expected_spec)
        self.assertEqual(notification["task_spec"], expected_spec)
        self.assertEqual(notification["task_spec_sha256"], expected_digest)
        self.assertEqual(notification["action_id"], expected_digest)
        self.assertEqual(notification["task_schema_version"], 1)
        self.assertTrue(notification["created_by"].startswith("openclaw:"))
        self.assertEqual(notification["title"], "Approval Required: OperaVPS Website Inspection")
        self.assertEqual(
            notification["message"],
            "Support Agent requests human authorization to open the OperaVPS website and inspect its public pages using browser automation. "
            "Public pages only; no logins, ticket submissions, order modifications, or account actions. "
            "Task will not begin until approval is verified.",
        )

        decision_url = f"/api/v1/notifications/{notification['id']}/approval"
        approval = self.client.get(decision_url, headers=headers)
        self.assertEqual(approval.status_code, 200, approval.text)
        self.assertEqual(approval.json()["task_spec_sha256"], expected_digest)
        self.assertEqual(approval.json()["task_specification"], expected_spec)
        self.assertEqual(approval.json()["task_spec"], expected_spec)
        self.assertEqual(approval.json()["action_id"], expected_digest)
        self.assertEqual(approval.json()["task_schema_version"], 1)
        self.assertEqual(self.client.put(f"/api/v1/notifications/{notification['id']}", headers=self.admin_headers, json={"task_specification": {}}).status_code, 405)

        unicode_spec = {"version": 1, "task_type": "public_website_inspection", "url": "https://example.org/café"}
        unicode_created = self.client.post("/api/v1/notifications", headers=headers, json={
            "source": "openclaw", "title": "Inspect", "message": "Display text", "requires_approval": True,
            "task_specification": unicode_spec,
        })
        self.assertEqual(unicode_created.status_code, 201, unicode_created.text)
        unicode_canonical = json.dumps(unicode_spec, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        self.assertEqual(unicode_created.json()["task_spec_sha256"], hashlib.sha256(unicode_canonical.encode("utf-8")).hexdigest())
        self.assertEqual(unicode_created.json()["title"], "Approval Required: Example Website Inspection")
        self.assertIn("open the Example website", unicode_created.json()["message"])

        approved = self.client.post(f"/api/v1/notifications/{notification['id']}/approve", headers=self.user_headers)
        self.assertEqual(approved.status_code, 200, approved.text)
        self.assertEqual(approved.json()["approved_by"], "viewer")
        self.assertIsNotNone(approved.json()["approved_at"])
        from openclaw_core_reference import parse_task_spec, verify_approval
        approved_response = self.client.get(decision_url, headers=headers)
        self.assertEqual(approved_response.status_code, 200, approved_response.text)
        expiry = verify_approval(
            approved_response.json(),
            notification_id=notification["id"],
            action_id=expected_digest,
            spec=parse_task_spec(expected_spec),
        )
        self.assertIsNotNone(expiry.tzinfo)

    def test_task_bound_creation_rejects_unsupported_or_unsafe_specs_and_client_decisions(self):
        headers = {"Authorization": "Bearer openclaw-test-key"}
        base = {"source": "openclaw", "title": "Inspect", "message": "Review", "requires_approval": True}
        invalid_specs = [
            {"version": 1, "task_type": "shell", "url": "https://example.com/"},
            {"version": 1, "task_type": "public_website_inspection", "url": "https://user:secret@example.com/"},
            {"version": 1, "task_type": "public_website_inspection", "url": "http://127.0.0.1/"},
            {"version": 1, "task_type": "public_website_inspection", "url": "https://example.com/#fragment"},
            {"version": 1, "task_type": "public_website_inspection", "url": "https://example.com/", "command": "whoami"},
        ]
        for specification in invalid_specs:
            response = self.client.post("/api/v1/notifications", headers=headers, json={**base, "task_spec": specification})
            self.assertEqual(response.status_code, 422, response.text)
        with_decision = self.client.post("/api/v1/notifications", headers=headers, json={
            **base, "approval_status": "pending", "task_spec": invalid_specs[1],
        })
        self.assertEqual(with_decision.status_code, 422)

    def test_task_binding_corruption_fails_closed(self):
        created = self.client.post("/api/v1/notifications", headers={"Authorization": "Bearer openclaw-test-key"}, json={
            "source": "openclaw", "title": "Inspect", "message": "Review", "requires_approval": True,
            "task_spec": {"version": 1, "task_type": "public_website_inspection", "url": "https://example.com/"},
        })
        self.assertEqual(created.status_code, 201, created.text)
        item = created.json()
        with self.sessions.begin() as db:
            row = db.get(models.Notification, item["id"])
            row.task_specification = row.task_specification.replace("example.com", "other.example")
        response = self.client.get(f"/api/v1/notifications/{item['id']}/approval", headers={"Authorization": "Bearer openclaw-test-key"})
        self.assertEqual(response.status_code, 409)
        approved = self.client.post(f"/api/v1/notifications/{item['id']}/approve", headers=self.user_headers)
        self.assertEqual(approved.status_code, 409)

    def test_expired_task_response_still_contains_spec_for_executor_expiry_gate(self):
        headers = {"Authorization": "Bearer openclaw-test-key"}
        created = self.client.post("/api/v1/notifications", headers=headers, json={
            "source": "openclaw", "title": "Inspect", "message": "Review", "requires_approval": True,
            "task_spec": {"version": 1, "task_type": "public_website_inspection", "url": "https://example.org/"},
        })
        self.assertEqual(created.status_code, 201, created.text)
        item = created.json()
        with self.sessions.begin() as db:
            db.get(models.Notification, item["id"]).approval_expires_at = datetime.utcnow() - timedelta(seconds=1)
        response = self.client.get(f"/api/v1/notifications/{item['id']}/approval", headers=headers)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["task_spec"], item["task_spec"])
        self.assertEqual(response.json()["task_spec_sha256"], item["task_spec_sha256"])
        rejected = self.client.post(f"/api/v1/notifications/{item['id']}/approve", headers=self.admin_headers)
        self.assertEqual(rejected.status_code, 410)

    def test_concurrent_task_decisions_allow_only_one_transition(self):
        created = self.client.post("/api/v1/notifications", headers={"Authorization": "Bearer openclaw-test-key"}, json={
            "source": "openclaw", "title": "Inspect", "message": "Review", "requires_approval": True,
            "task_spec": {"version": 1, "task_type": "public_website_inspection", "url": "https://example.com/"},
        })
        self.assertEqual(created.status_code, 201, created.text)
        path = f"/api/v1/notifications/{created.json()['id']}/approve"
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(pool.map(lambda _: self.client.post(path, headers=self.user_headers), range(2)))
        self.assertEqual(sorted(response.status_code for response in responses), [200, 409])

    def test_openclaw_approval_decision_endpoint_is_key_owned_action_bound_and_read_only(self):
        headers = {"Authorization": "Bearer openclaw-test-key"}
        created = self.client.post(
            "/api/v1/notifications",
            headers=headers,
            json={
                "source": "openclaw",
                "title": "Approval Required",
                "message": "Deploy service alpha",
                "requires_approval": True,
                "task_id": "deploy-alpha-42",
                "metadata": {"service": "alpha", "version": "4.2"},
            },
        )
        self.assertEqual(created.status_code, 201, created.text)
        approval = created.json()
        self.assertEqual(len(approval["action_id"]), 64)
        self.assertIsNotNone(approval["approval_expires_at"])

        path = f"/api/v1/notifications/{approval['id']}/approval"
        self.client.cookies.set(SESSION_COOKIE_NAME, create_access_token("admin"))
        self.assertEqual(self.client.get(path).status_code, 401)
        self.client.cookies.clear()
        self.assertEqual(self.client.get(path, headers={"Authorization": "Bearer wrong"}).status_code, 401)
        pending = self.client.get(path, headers=headers)
        self.assertEqual(pending.status_code, 200, pending.text)
        self.assertEqual(pending.json()["approval_status"], "pending")
        self.assertTrue(pending.json()["requires_approval"])
        self.assertEqual(pending.json()["action_id"], approval["action_id"])
        self.assertEqual(
            set(pending.json()),
            {"notification_id", "requires_approval", "approval_status", "action_id", "approval_expires_at"},
        )
        mismatch = self.client.get(f"{path}?action_id={'0' * 64}", headers=headers)
        self.assertEqual(mismatch.status_code, 404)

        db = self.sessions()
        try:
            row = db.get(models.Notification, approval["id"])
            original = (row.approval_status, row.updated_at, row.approved_at)
        finally:
            db.close()
        self.assertEqual(self.client.get(path, headers=headers).json()["approval_status"], "pending")
        self.assertEqual(self.client.get(path, headers=headers).json()["approval_status"], "pending")
        db = self.sessions()
        try:
            row = db.get(models.Notification, approval["id"])
            self.assertEqual((row.approval_status, row.updated_at, row.approved_at), original)
        finally:
            db.close()

        self.assertEqual(self.client.post(f"/api/v1/notifications/{approval['id']}/approve", headers=headers).status_code, 401)
        self.assertEqual(self.client.post(f"/api/v1/notifications/{approval['id']}/deny", headers=headers).status_code, 401)
        approved = self.client.post(f"/api/v1/notifications/{approval['id']}/approve", headers=self.admin_headers)
        self.assertEqual(approved.status_code, 200, approved.text)
        decision = self.client.get(path, headers=headers)
        self.assertEqual(decision.status_code, 200, decision.text)
        self.assertEqual(decision.json()["approval_status"], "approved")

        # The dedicated key is bound to the owner fingerprint stored at creation.
        with patch.object(settings, "openclaw_notification_api_key", "rotated-openclaw-key"):
            self.assertEqual(
                self.client.get(path, headers={"Authorization": "Bearer rotated-openclaw-key"}).status_code,
                404,
            )

    def test_openclaw_approval_decision_returns_denied_and_hides_non_owned_records(self):
        headers = {"Authorization": "Bearer openclaw-test-key"}
        created = self.client.post(
            "/api/v1/notifications",
            headers=headers,
            json={"source": "openclaw", "title": "Delete account", "message": "Delete account 17", "requires_approval": True},
        )
        approval = created.json()
        denied = self.client.post(
            f"/api/v1/notifications/{approval['id']}/deny",
            headers=self.admin_headers,
            json={"reason": "Not approved"},
        )
        self.assertEqual(denied.status_code, 200, denied.text)
        decision = self.client.get(f"/api/v1/notifications/{approval['id']}/approval", headers=headers)
        self.assertEqual(decision.status_code, 200, decision.text)
        self.assertEqual(decision.json()["approval_status"], "denied")

        ordinary = self.client.post(
            "/api/v1/notifications",
            headers=headers,
            json={"source": "openclaw", "title": "FYI", "message": "No approval needed"},
        ).json()
        non_approval = self.client.get(f"/api/v1/notifications/{ordinary['id']}/approval", headers=headers)
        self.assertEqual(non_approval.status_code, 404)

        admin_test = self.client.post("/api/v1/notifications/test", headers=self.admin_headers).json()
        hidden = self.client.get(f"/api/v1/notifications/{admin_test['id']}/approval", headers=headers)
        self.assertEqual(hidden.status_code, 404)
        missing = self.client.get("/api/v1/notifications/99999/approval", headers=headers)
        self.assertEqual(missing.status_code, 404)

    def test_expired_approval_cannot_be_retrieved_or_approved(self):
        headers = {"Authorization": "Bearer openclaw-test-key"}
        created = self.client.post(
            "/api/v1/notifications",
            headers=headers,
            json={"source": "openclaw", "title": "Restart", "message": "Restart server 3", "requires_approval": True},
        )
        approval = created.json()
        db = self.sessions()
        try:
            row = db.get(models.Notification, approval["id"])
            row.approval_expires_at = datetime.utcnow() - timedelta(seconds=1)
            db.commit()
        finally:
            db.close()

        path = f"/api/v1/notifications/{approval['id']}/approval"
        self.assertEqual(self.client.get(path, headers=headers).status_code, 410)
        admin_response = self.client.post(f"/api/v1/notifications/{approval['id']}/approve", headers=self.admin_headers)
        self.assertEqual(admin_response.status_code, 410)
        db = self.sessions()
        try:
            self.assertEqual(db.get(models.Notification, approval["id"]).approval_status, "pending")
        finally:
            db.close()

    def test_legacy_approval_without_binding_metadata_is_not_authorized(self):
        from app.notifications.service import create_notification
        legacy = create_notification(
            source="openclaw",
            title="Legacy request",
            message="Old approval record",
            requires_approval=True,
        )
        response = self.client.get(
            f"/api/v1/notifications/{legacy.id}/approval",
            headers={"Authorization": "Bearer openclaw-test-key"},
        )
        self.assertEqual(response.status_code, 404)

    def test_approval_expiration_must_be_future_and_non_approval_cannot_set_expiry(self):
        headers = {"Authorization": "Bearer openclaw-test-key"}
        past = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
        expired = self.client.post(
            "/api/v1/notifications",
            headers=headers,
            json={"source": "openclaw", "title": "Action", "message": "Do action", "requires_approval": True, "approval_expires_at": past},
        )
        self.assertEqual(expired.status_code, 422)
        invalid = self.client.post(
            "/api/v1/notifications",
            headers=headers,
            json={"source": "openclaw", "title": "FYI", "message": "No approval", "approval_expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()},
        )
        self.assertEqual(invalid.status_code, 422)

    def test_migration_adds_nullable_approval_fields_without_backfilling_legacy_rows(self):
        from app.models import _migrate_notification_approval_fields
        with tempfile.TemporaryDirectory() as root:
            legacy_engine = create_engine(f"sqlite:///{Path(root) / 'legacy.db'}")
            try:
                with legacy_engine.begin() as conn:
                    conn.exec_driver_sql(
                        "CREATE TABLE notifications (id INTEGER PRIMARY KEY, source VARCHAR(30), requires_approval BOOLEAN, approval_status VARCHAR(20))"
                    )
                    conn.exec_driver_sql("INSERT INTO notifications (id, source, requires_approval, approval_status) VALUES (1, 'openclaw', 1, 'pending')")
                _migrate_notification_approval_fields(legacy_engine)
                _migrate_notification_approval_fields(legacy_engine)
                with legacy_engine.connect() as conn:
                    columns = {row["name"] for row in inspect(legacy_engine).get_columns("notifications")}
                    row = conn.exec_driver_sql("SELECT action_id, approval_expires_at, approval_owner_hash FROM notifications WHERE id = 1").one()
                self.assertTrue({"action_id", "approval_expires_at", "approval_owner_hash", "task_specification", "task_spec_sha256", "task_schema_version", "task_type", "created_by"}.issubset(columns))
                self.assertEqual(row, (None, None, None))
            finally:
                legacy_engine.dispose()

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
