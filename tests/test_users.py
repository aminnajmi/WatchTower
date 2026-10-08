import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import auth, main, models
from app.auth import create_access_token, generate_password_hash, hash_user_password, verify_user_password
from app.config import settings
from app.models import Base, OSRelease, User


class UserManagementTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.engine = create_engine(f"sqlite:///{Path(self.temp_dir.name) / 'users.db'}")
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)
        with self.sessions.begin() as db:
            db.add_all([
                User(username="admin", password_hash=hash_user_password("correct-admin-password"), role="admin", is_active=True),
                User(username="viewer", password_hash=hash_user_password("correct-viewer-password"), role="user", is_active=True),
            ])
        self.patches = [
            patch.object(main, "SessionLocal", self.sessions),
            patch.object(auth, "SessionLocal", self.sessions),
            patch.object(main, "init_db"),
            patch.object(main, "start_scheduler"),
            patch.object(main, "stop_scheduler"),
            patch.object(settings, "jwt_secret", "watchtower-user-tests-secret-with-32-bytes-minimum"),
            patch.object(settings, "admin_username", "admin"),
        ]
        for item in self.patches:
            item.start()
        self.client = TestClient(main.app)
        self.client.__enter__()
        self.admin_token = create_access_token("admin")
        self.user_token = create_access_token("viewer")
        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
        self.user_headers = {"Authorization": f"Bearer {self.user_token}"}

    def tearDown(self):
        self.client.__exit__(None, None, None)
        for item in reversed(self.patches):
            item.stop()
        self.engine.dispose()
        self.temp_dir.cleanup()

    def test_admin_and_user_login_disabled_login_and_invalid_credentials(self):
        admin = self.client.post("/api/v1/auth/token", data={"username": "admin", "password": "correct-admin-password"})
        user = self.client.post("/api/v1/auth/token", data={"username": "viewer", "password": "correct-viewer-password"})
        invalid = self.client.post("/api/v1/auth/token", data={"username": "viewer", "password": "wrong-password"})
        self.assertEqual(admin.status_code, 200)
        self.assertEqual(admin.json()["user"]["role"], "admin")
        self.assertEqual(user.status_code, 200)
        self.assertEqual(user.json()["user"]["role"], "user")
        self.assertEqual(invalid.status_code, 401)
        with self.sessions.begin() as db:
            db.query(User).filter_by(username="viewer").one().is_active = False
        self.assertEqual(self.client.post("/api/v1/auth/token", data={"username": "viewer", "password": "correct-viewer-password"}).status_code, 401)
        self.assertEqual(self.client.get("/api/v1/os", headers=self.user_headers).status_code, 401)

    def test_admin_only_routes_and_unauthenticated_rejection(self):
        self.assertEqual(self.client.get("/api/v1/users").status_code, 401)
        self.assertEqual(self.client.get("/api/v1/users", headers=self.user_headers).status_code, 403)
        with self.sessions() as db:
            viewer_id = db.query(User).filter_by(username="viewer").one().id
        self.assertEqual(self.client.patch(f"/api/v1/users/{viewer_id}", headers=self.user_headers, json={"role": "admin"}).status_code, 403)
        self.assertEqual(self.client.post("/api/v1/check", headers=self.user_headers).status_code, 403)
        self.assertEqual(self.client.post("/api/v1/notifications/test/telegram", headers=self.user_headers).status_code, 403)
        self.client.post("/web/session", json={"access_token": self.admin_token})
        self.assertEqual(self.client.get("/users").status_code, 200)
        self.assertEqual(self.client.get("/account").status_code, 200)
        self.assertIn('href="/users"', self.client.get("/dashboard").text)
        self.client.post("/web/session", json={"access_token": self.user_token})
        self.assertEqual(self.client.get("/users").status_code, 403)
        self.assertEqual(self.client.get("/settings").status_code, 403)
        self.assertEqual(self.client.get("/notification-center").status_code, 200)
        for path in ("/dashboard", "/os", "/os/ubuntu", "/releases", "/events"):
            with self.subTest(path=path):
                response = self.client.get(path, follow_redirects=False)
                self.assertEqual(response.status_code, 303)
                self.assertEqual(response.headers["location"], "/notification-center")
        notification_center = self.client.get("/notification-center").text
        self.assertNotIn('href="/users"', notification_center)
        self.assertNotIn('href="/dashboard"', notification_center)
        self.assertNotIn('href="/os"', notification_center)
        self.assertNotIn('href="/releases"', notification_center)
        self.assertNotIn('href="/events"', notification_center)
        self.assertNotIn("Sound OFF", notification_center)
        self.assertNotIn("notification-sound-toggle", notification_center)
        for path in ("/api/v1/os", "/api/v1/releases", "/api/v1/events", "/api/v1/providers", "/api/v1/status"):
            with self.subTest(api=path):
                self.assertEqual(self.client.get(path, headers=self.user_headers).status_code, 403)

    def test_create_edit_password_reset_enable_disable_and_delete(self):
        payload = {
            "username": "new.viewer", "password": "initial-user-password", "confirm_password": "initial-user-password",
            "role": "User", "is_active": True,
        }
        created = self.client.post("/api/v1/users", headers=self.admin_headers, json=payload)
        self.assertEqual(created.status_code, 201, created.text)
        user = created.json()
        user_id = user["id"]
        self.assertNotIn("password", user)
        self.assertNotIn("password_hash", user)
        self.assertEqual(user["role"], "user")
        self.assertIsNotNone(user["created_at"])
        self.assertNotIn("password_hash", self.client.get("/api/v1/users", headers=self.admin_headers).text)
        duplicate = self.client.post("/api/v1/users", headers=self.admin_headers, json=payload)
        self.assertEqual(duplicate.status_code, 409)

        with self.sessions() as db:
            stored = db.get(User, user_id)
            self.assertNotEqual(stored.password_hash, payload["password"])
            self.assertTrue(verify_user_password(payload["password"], stored.password_hash))

        updated = self.client.patch(f"/api/v1/users/{user_id}", headers=self.admin_headers, json={"username": "new.viewer2", "role": "Admin"})
        self.assertEqual(updated.status_code, 200)
        self.assertEqual((updated.json()["username"], updated.json()["role"]), ("new.viewer2", "admin"))

        old_login = self.client.post("/api/v1/auth/token", data={"username": "new.viewer2", "password": payload["password"]})
        self.assertEqual(old_login.status_code, 200)
        token = old_login.json()["access_token"]
        disabled = self.client.post(f"/api/v1/users/{user_id}/disable", headers=self.admin_headers)
        self.assertEqual(disabled.status_code, 200)
        self.assertFalse(disabled.json()["is_active"])
        self.assertEqual(self.client.get("/api/v1/os", headers={"Authorization": f"Bearer {token}"}).status_code, 401)
        self.assertEqual(self.client.post("/api/v1/auth/token", data={"username": "new.viewer2", "password": payload["password"]}).status_code, 401)
        self.assertTrue(self.client.post(f"/api/v1/users/{user_id}/enable", headers=self.admin_headers).json()["is_active"])

        reset_password = "replacement-user-password"
        reset = self.client.post(f"/api/v1/users/{user_id}/reset-password", headers=self.admin_headers, json={"new_password": reset_password, "confirm_password": reset_password})
        self.assertEqual(reset.status_code, 200)
        self.assertEqual(self.client.post("/api/v1/auth/token", data={"username": "new.viewer2", "password": payload["password"]}).status_code, 401)
        self.assertEqual(self.client.post("/api/v1/auth/token", data={"username": "new.viewer2", "password": reset_password}).status_code, 200)

        deleted = self.client.delete(f"/api/v1/users/{user_id}", headers=self.admin_headers)
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(self.client.get(f"/api/v1/users/{user_id}", headers=self.admin_headers).status_code, 404)

    def test_last_admin_and_self_protection(self):
        with self.sessions() as db:
            admin_id = db.query(User).filter_by(username="admin").one().id
        self.assertEqual(self.client.post(f"/api/v1/users/{admin_id}/disable", headers=self.admin_headers).status_code, 409)
        self.assertEqual(self.client.patch(f"/api/v1/users/{admin_id}", headers=self.admin_headers, json={"role": "user"}).status_code, 409)
        self.assertEqual(self.client.delete(f"/api/v1/users/{admin_id}", headers=self.admin_headers).status_code, 409)

        with self.sessions.begin() as db:
            db.add(User(username="backup-admin", password_hash=hash_user_password("backup-admin-password"), role="admin", is_active=True))
        backup_login = self.client.post("/api/v1/auth/token", data={"username": "backup-admin", "password": "backup-admin-password"})
        backup_headers = {"Authorization": f"Bearer {backup_login.json()['access_token']}"}
        self.assertEqual(self.client.post(f"/api/v1/users/{admin_id}/disable", headers=backup_headers).status_code, 200)
        self.assertEqual(self.client.delete(f"/api/v1/users/{admin_id}", headers=backup_headers).status_code, 200)

    def test_password_change_and_validation_errors_never_echo_password(self):
        response = self.client.post(
            "/api/v1/account/change-password", headers=self.user_headers,
            json={"current_password": "correct-viewer-password", "new_password": "updated-viewer-password", "confirm_password": "mismatched-password"},
        )
        self.assertEqual(response.status_code, 422)
        self.assertNotIn("updated-viewer-password", response.text)
        self.assertNotIn("correct-viewer-password", response.text)
        changed = self.client.post(
            "/api/v1/account/change-password", headers=self.user_headers,
            json={"current_password": "correct-viewer-password", "new_password": "updated-viewer-password", "confirm_password": "updated-viewer-password"},
        )
        self.assertEqual(changed.status_code, 200)
        self.assertEqual(self.client.post("/api/v1/auth/token", data={"username": "viewer", "password": "updated-viewer-password"}).status_code, 200)

    def test_bad_login_does_not_log_submitted_password(self):
        secret = "never-write-this-password"
        with self.assertLogs("app.main", level="WARNING") as captured:
            self.client.post("/api/v1/auth/token", data={"username": "viewer", "password": secret})
        self.assertNotIn(secret, "\n".join(captured.output))

    def test_existing_environment_admin_is_bootstrapped_without_replacing_release_data(self):
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "legacy.db"
            engine = create_engine(f"sqlite:///{database_path}")
            Base.metadata.create_all(engine)
            sessions = sessionmaker(bind=engine, autoflush=False, autocommit=False)
            with sessions.begin() as db:
                db.add(OSRelease(
                    slug="ubuntu", name="Ubuntu", version="24.04", major_version="24",
                    source_url="https://ubuntu.com", release_type="major",
                ))
            password_hash, salt = generate_password_hash("bootstrap-admin-password")
            with patch.object(models, "engine", engine), \
                 patch.object(settings, "database_url", f"sqlite:///{database_path}"), \
                 patch.object(settings, "admin_username", "bootstrap-admin"), \
                 patch.object(settings, "admin_password_hash", password_hash), \
                 patch.object(settings, "admin_password_salt", salt):
                models.init_db()
            with sessions() as db:
                admin = db.query(User).filter_by(username="bootstrap-admin").one()
                ubuntu = db.query(OSRelease).filter_by(slug="ubuntu").one()
                self.assertEqual(admin.role, "admin")
                self.assertTrue(verify_user_password("bootstrap-admin-password", admin.password_hash))
                self.assertEqual(ubuntu.version, "24.04")
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
