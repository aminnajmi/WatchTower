import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app import auth, main, todos
from app.auth import create_access_token, hash_user_password
from app.config import settings
from app.models import Base, Notification, Todo, User


class TodoTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.engine = create_engine(f"sqlite:///{Path(self.temp_dir.name) / 'todos.db'}", connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)
        with self.sessions.begin() as db:
            db.add_all([
                User(username=name, password_hash=hash_user_password(f"test-{name}-password"), role="admin" if name == "admin" else "user", is_active=True)
                for name in ("admin", "alice", "bob", "carol")
            ])
        self.patches = [
            patch.object(todos, "SessionLocal", self.sessions), patch.object(auth, "SessionLocal", self.sessions),
            patch.object(main, "SessionLocal", self.sessions), patch.object(main, "init_db"),
            patch.object(main, "start_scheduler"), patch.object(main, "stop_scheduler"),
            patch.object(settings, "jwt_secret", "watchtower-todo-tests-secret-long-enough"),
        ]
        for item in self.patches:
            item.start()
        self.client = TestClient(main.app)
        self.client.__enter__()
        self.tokens = {name: {"Authorization": f"Bearer {create_access_token(name)}"} for name in ("admin", "alice", "bob", "carol")}
        with self.sessions() as db:
            self.ids = {user.username: user.id for user in db.scalars(select(User)).all()}

    def tearDown(self):
        self.client.__exit__(None, None, None)
        for item in reversed(self.patches):
            item.stop()
        self.engine.dispose()
        self.temp_dir.cleanup()

    def create(self, who="alice", **overrides):
        return self.client.post("/api/v1/todos", headers=self.tokens[who], json={"title": "Prepare release", "description": "Coordinate rollout", **overrides})

    def test_auth_visibility_and_assignment_notification_idempotence(self):
        self.assertEqual(self.client.get("/api/v1/todos").status_code, 401)
        response = self.create(assigned_to_user_id=self.ids["bob"])
        self.assertEqual(response.status_code, 201, response.text)
        item = response.json()
        self.assertEqual(item["created_by"]["username"], "alice")
        self.assertEqual(item["assigned_to"]["username"], "bob")
        self.assertEqual(self.client.get("/api/v1/todos", headers=self.tokens["carol"]).json()["total"], 0)
        self.assertEqual(self.client.get(f"/api/v1/todos/{item['id']}", headers=self.tokens["bob"]).status_code, 200)
        self.client.patch(f"/api/v1/todos/{item['id']}", headers=self.tokens["alice"], json={"assigned_to_user_id": self.ids["bob"]})
        with self.sessions() as db:
            notices = db.scalars(select(Notification).where(Notification.task_id == str(item["id"]))).all()
        self.assertEqual(len(notices), 1)
        self.assertEqual(notices[0].recipient, "bob")
        self.assertNotIn(notices[0].id, [n["id"] for n in self.client.get("/api/v1/notifications", headers=self.tokens["alice"]).json()["items"]])
        self.assertIn(notices[0].id, [n["id"] for n in self.client.get("/api/v1/notifications", headers=self.tokens["bob"]).json()["items"]])
        self.client.patch(f"/api/v1/todos/{item['id']}", headers=self.tokens["alice"], json={"assigned_to_user_id": self.ids["carol"]})
        self.client.patch(f"/api/v1/todos/{item['id']}", headers=self.tokens["alice"], json={"assigned_to_user_id": self.ids["carol"]})
        with self.sessions() as db:
            notices = db.scalars(select(Notification).where(Notification.task_id == str(item["id"]))).all()
        self.assertEqual([notice.recipient for notice in notices], ["bob", "carol"])
        self.assertEqual(self.client.get(f"/api/v1/todos/{item['id']}", headers=self.tokens["bob"]).status_code, 404)
        self.assertEqual(self.client.get(f"/api/v1/todos/{item['id']}", headers=self.tokens["carol"]).status_code, 200)

    def test_permissions_completion_reopen_filters_and_summary(self):
        item = self.create(assigned_to_user_id=self.ids["bob"], due_date=(datetime.utcnow() + timedelta(days=1)).isoformat()).json()
        url = f"/api/v1/todos/{item['id']}"
        self.assertEqual(self.client.patch(url, headers=self.tokens["carol"], json={"title": "forbidden"}).status_code, 404)
        self.assertEqual(self.client.patch(url, headers=self.tokens["bob"], json={"title": "forbidden"}).status_code, 403)
        done = self.client.patch(url, headers=self.tokens["bob"], json={"is_completed": True})
        self.assertTrue(done.json()["is_completed"])
        self.assertIsNotNone(done.json()["completed_at"])
        reopened = self.client.patch(url, headers=self.tokens["bob"], json={"is_completed": False})
        self.assertIsNone(reopened.json()["completed_at"])
        self.assertEqual(self.client.get("/api/v1/todos?view=my", headers=self.tokens["bob"]).json()["total"], 1)
        self.assertEqual(self.client.get("/api/v1/todos?q=rollout", headers=self.tokens["alice"]).json()["total"], 1)
        self.assertEqual(self.client.get("/api/v1/todos?q=not-found", headers=self.tokens["alice"]).json()["total"], 0)
        summary = self.client.get("/api/v1/todos/summary", headers=self.tokens["alice"]).json()
        self.assertEqual((summary["my_pending"], summary["assigned_by_me"], summary["my_total"], summary["total"]), (0, 1, 0, 1))
        self.assertEqual(self.client.delete(url, headers=self.tokens["bob"]).status_code, 403)
        self.assertEqual(self.client.delete(url, headers=self.tokens["alice"]).status_code, 204)

    def test_active_assignee_validation_and_admin_access(self):
        self.assertEqual(self.create(assigned_to_user_id=9999).status_code, 422)
        item = self.create().json()
        response = self.client.patch(f"/api/v1/todos/{item['id']}", headers=self.tokens["admin"], json={"title": "Admin edit"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/api/v1/todos", headers=self.tokens["admin"]).json()["total"], 1)

    def test_sorting_pagination_and_pending_filter_preserve_visibility(self):
        first = self.create(title="Zulu", assigned_to_user_id=self.ids["alice"], due_date="2030-06-03T12:00:00Z").json()
        second = self.create(title="alpha", assigned_to_user_id=self.ids["carol"], due_date="2030-06-01T12:00:00Z").json()
        third = self.create(title="Beta", assigned_to_user_id=self.ids["bob"]).json()
        self.create(who="carol", title="Hidden", due_date="2029-01-01T12:00:00Z")
        for sort, expected in {
            "title": [second, third, first],
            "due_date": [second, first, third],
            "created_at": [third, second, first],
            "assignee": [first, third, second],
        }.items():
            with self.subTest(sort=sort):
                pages = [self.client.get(f"/api/v1/todos?sort={sort}&limit=1&offset={offset}", headers=self.tokens["alice"]).json() for offset in range(3)]
                self.assertEqual([page["items"][0]["id"] for page in pages], [item["id"] for item in expected])
                self.assertTrue(all(page["total"] == 3 for page in pages))
        self.client.patch(f"/api/v1/todos/{second['id']}", headers=self.tokens["admin"], json={"is_completed": True})
        pending = self.client.get("/api/v1/todos?view=pending&q=rollout&sort=title", headers=self.tokens["alice"]).json()
        self.assertEqual([item["id"] for item in pending["items"]], [third["id"], first["id"]])
        self.assertEqual(self.client.get("/api/v1/todos?sort=invalid", headers=self.tokens["alice"]).status_code, 422)

    def test_additive_schema_preserves_users_and_old_tables(self):
        with self.sessions() as db:
            db.add(Todo(title="Existing record", created_by_user_id=self.ids["alice"], created_by_name="alice"))
            db.commit()
        Base.metadata.create_all(self.engine)
        with self.sessions() as db:
            self.assertEqual(db.scalar(select(User.username).where(User.id == self.ids["alice"])), "alice")
            self.assertEqual(db.scalar(select(Todo.title)), "Existing record")
        with self.engine.connect() as conn:
            tables = set(__import__("sqlalchemy").inspect(self.engine).get_table_names())
            self.assertIn("todos", tables)
            self.assertIn("notifications", tables)


if __name__ == "__main__":
    unittest.main()
