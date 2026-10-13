import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app import auth, main, tasks
from app.auth import create_access_token, hash_user_password
from app.config import settings
from app.models import Base, Notification, Task, TaskActivity, TaskComment, TaskNotification, User


class TaskManagementTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.engine = create_engine(f"sqlite:///{Path(self.temp_dir.name) / 'tasks.db'}", connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)
        with self.sessions.begin() as db:
            db.add_all([
                User(username="admin", password_hash=hash_user_password("test-admin-password"), role="admin", is_active=True),
                User(username="alice", password_hash=hash_user_password("test-alice-password"), role="user", is_active=True),
                User(username="bob", password_hash=hash_user_password("test-bob-password"), role="user", is_active=True),
                User(username="carol", password_hash=hash_user_password("test-carol-password"), role="user", is_active=True),
            ])
        self.patches = [
            patch.object(tasks, "SessionLocal", self.sessions), patch.object(auth, "SessionLocal", self.sessions),
            patch.object(main, "SessionLocal", self.sessions), patch.object(main, "init_db"),
            patch.object(main, "start_scheduler"),
            patch.object(main, "stop_scheduler"), patch.object(settings, "jwt_secret", "watchtower-task-tests-secret-long-enough"),
        ]
        for item in self.patches: item.start()
        self.client = TestClient(main.app); self.client.__enter__()
        self.tokens = {name: {"Authorization": f"Bearer {create_access_token(name)}"} for name in ("admin", "alice", "bob", "carol")}
        with self.sessions() as db:
            self.ids = {u.username: u.id for u in db.scalars(select(User)).all()}

    def tearDown(self):
        self.client.__exit__(None, None, None)
        for item in reversed(self.patches): item.stop()
        self.engine.dispose(); self.temp_dir.cleanup()

    def create(self, who="alice", **overrides):
        payload = {"title": "Prepare release", "description": "Coordinate the rollout", "assignee_ids": [self.ids["alice"], self.ids["bob"]], "priority": "high", **overrides}
        return self.client.post("/api/v1/tasks", headers=self.tokens[who], json=payload)

    def test_auth_creation_multi_assignment_and_activity(self):
        self.assertEqual(self.client.get("/api/v1/tasks").status_code, 401)
        response = self.create()
        self.assertEqual(response.status_code, 201, response.text)
        task = response.json(); self.assertEqual(len(task["assignees"]), 2)
        self.assertEqual(task["creator"]["username"], "alice")
        self.assertEqual(self.client.get("/api/v1/tasks", headers=self.tokens["carol"]).json()["total"], 0)
        detail = self.client.get(f"/api/v1/tasks/{task['id']}", headers=self.tokens["bob"])
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["activity"][0]["action"], "created")

    def test_permissions_status_comment_assignment_and_delete(self):
        task = self.create().json(); task_id = task["id"]
        self.assertEqual(self.client.patch(f"/api/v1/tasks/{task_id}", headers=self.tokens["carol"], json={"title": "forbidden"}).status_code, 404)
        self.assertEqual(self.client.patch(f"/api/v1/tasks/{task_id}", headers=self.tokens["bob"], json={"priority": "urgent"}).status_code, 403)
        self.assertEqual(self.client.patch(f"/api/v1/tasks/{task_id}", headers=self.tokens["bob"], json={"status": "in_progress"}).status_code, 200)
        comment = self.client.post(f"/api/v1/tasks/{task_id}/comments", headers=self.tokens["bob"], json={"body": "I am on it"})
        self.assertEqual(comment.status_code, 201)
        self.assertEqual(self.client.delete(f"/api/v1/tasks/{task_id}", headers=self.tokens["bob"]).status_code, 403)
        reassigned = self.client.post(f"/api/v1/tasks/{task_id}/assign", headers=self.tokens["alice"], json={"assignee_ids": [self.ids["carol"]]})
        self.assertEqual(reassigned.status_code, 200)
        self.assertEqual([u["username"] for u in reassigned.json()["assignees"]], ["carol"])
        self.assertTrue(any(item["ended_at"] for item in reassigned.json()["assignment_history"]))
        self.assertEqual(self.client.delete(f"/api/v1/tasks/{task_id}", headers=self.tokens["alice"]).status_code, 204)

    def test_filters_summary_and_completion_timestamp(self):
        due = (datetime.utcnow() + timedelta(hours=2)).isoformat()
        task = self.create(due_at=due).json()
        filtered = self.client.get("/api/v1/tasks?priority=high&assignee_id=%s" % self.ids["bob"], headers=self.tokens["alice"])
        self.assertEqual(filtered.json()["total"], 1)
        done = self.client.post(f"/api/v1/tasks/{task['id']}/status", headers=self.tokens["bob"], json={"status": "completed"})
        self.assertEqual(done.status_code, 200); self.assertIsNotNone(done.json()["completed_at"])
        self.assertEqual(self.client.get("/api/v1/tasks/summary", headers=self.tokens["carol"]).json()["total"], 0)

    def test_deadline_notifications_are_isolated_and_idempotent(self):
        task = self.create(assignee_ids=[self.ids["bob"]], due_at=(datetime.utcnow() - timedelta(hours=1)).isoformat()).json()
        tasks.check_task_deadlines(); tasks.check_task_deadlines()
        with self.sessions() as db:
            notices = db.scalars(select(Notification).where(Notification.task_id == str(task["id"]))).all()
            tracking = db.scalars(select(TaskNotification).where(TaskNotification.task_id == task["id"])).all()
        self.assertEqual({n.recipient for n in notices}, {"bob"})
        self.assertEqual(len(tracking), 2)  # one assignment notice and one overdue notice
        alice_feed = self.client.get("/api/v1/notifications", headers=self.tokens["alice"]).json()
        bob_feed = self.client.get("/api/v1/notifications", headers=self.tokens["bob"]).json()
        self.assertFalse(any(n["id"] == notices[0].id for n in alice_feed["items"]))
        self.assertTrue(any(n["id"] == notices[0].id for n in bob_feed["items"]))

    def test_additive_schema_creation_preserves_existing_users(self):
        path = Path(self.temp_dir.name) / "legacy.db"
        legacy = create_engine(f"sqlite:///{path}")
        User.__table__.create(legacy)
        with legacy.begin() as conn:
            conn.exec_driver_sql("INSERT INTO users (username, password_hash, role, is_active, created_at, updated_at) VALUES ('legacy', 'hash', 'user', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)")
        Base.metadata.create_all(legacy)
        with legacy.connect() as conn:
            self.assertEqual(conn.exec_driver_sql("SELECT username FROM users").scalar_one(), "legacy")
            tables = set(__import__("sqlalchemy").inspect(legacy).get_table_names())
            self.assertTrue({"tasks", "task_assignments", "task_comments", "task_activity", "task_notification_tracking"} <= tables)
        legacy.dispose()


if __name__ == "__main__":
    unittest.main()
