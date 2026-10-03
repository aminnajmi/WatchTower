import hashlib
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import main, service
from app.auth import SESSION_COOKIE_NAME, create_access_token, generate_password_hash
from app.config import settings
from app.models import Base, OSRelease, ReleaseHistory, ReleaseEvent
from app.providers.base import Release


class WebDashboardTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.engine = create_engine(f"sqlite:///{Path(self.temp_dir.name) / 'web.db'}")
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)
        with self.sessions() as db:
            ubuntu = OSRelease(
                slug="ubuntu", name="Ubuntu", version="26.04.1", major_version="26",
                source_url="https://ubuntu.com/download/server", release_type="minor", is_rolling=False,
            )
            db.add(ubuntu)
            db.flush()
            db.add_all([
                ReleaseHistory(os_id=ubuntu.id, version="26.04", major_version="26", release_type="major", release_date="2026-04-23", source_url="https://ubuntu.com", detected_at=datetime(2026, 4, 23)),
                ReleaseHistory(os_id=ubuntu.id, version="26.04.1", major_version="26", release_type="minor", release_date="2026-08-12", source_url="https://ubuntu.com", detected_at=datetime(2026, 8, 12)),
                ReleaseEvent(os_id=ubuntu.id, previous_version="26.04.1", new_version="28.04", previous_major_version="26", new_major_version="28", event_type="new_major_release"),
            ])
            db.commit()
        self.patches = [
            patch.object(main, "SessionLocal", self.sessions),
            patch.object(service, "SessionLocal", self.sessions),
            patch.object(main, "init_db"),
            patch.object(main, "start_scheduler"),
        ]
        for item in self.patches:
            item.start()
        service.last_check_result = None
        service.last_check_started_at = None
        service.last_check_finished_at = None
        self.client = TestClient(main.app)
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)
        for item in reversed(self.patches):
            item.stop()
        self.engine.dispose()
        self.temp_dir.cleanup()

    def sign_in(self):
        with patch.object(main, "verify_password", return_value=True):
            token_response = self.client.post(
                "/api/v1/auth/token",
                data={"username": settings.admin_username, "password": "test-password"},
            )
        self.assertEqual(token_response.status_code, 200)
        token = token_response.json()["access_token"]
        session_response = self.client.post("/web/session", json={"access_token": token})
        self.assertEqual(session_response.status_code, 200)
        self.session_response = session_response
        return token

    def test_login_page_and_existing_jwt_login_flow(self):
        page = self.client.get("/login")
        self.assertEqual(page.status_code, 200)
        self.assertIn("WatchTower", page.text)
        self.assertIn('id="login-form"', page.text)
        self.assertIn('method="post" action="/login"', page.text)
        version = hashlib.sha256(Path("static/js/app.js").read_bytes()).hexdigest()[:12]
        self.assertIn(f'/static/js/app.js?v={version}', page.text)
        self.assertNotIn("cdn.tailwindcss.com", page.text)
        script = (Path("static/js/app.js")).read_text()
        self.assertIn("/api/v1/auth/token", script)
        self.assertIn("/web/session", script)
        self.assertIn("Cannot connect to WatchTower", script)
        self.assertEqual(self.client.get("/static/js/app.js").status_code, 200)
        self.sign_in()
        cookie = self.client.cookies.get(SESSION_COOKIE_NAME)
        self.assertTrue(cookie)
        self.assertIn("httponly", self.session_response.headers.get("set-cookie", "").lower())

    def test_http_credentials_create_httponly_cookie_and_authenticated_dashboard(self):
        password = "test-password-for-http-login"
        password_hash, password_salt = generate_password_hash(password)
        with patch.object(settings, "jwt_secret", "watchtower-test-secret-with-at-least-32-bytes"), \
             patch.object(settings, "admin_username", "watchtower-test-admin"), \
             patch.object(settings, "admin_password_hash", password_hash), \
             patch.object(settings, "admin_password_salt", password_salt), \
             patch.object(settings, "access_token_expire_minutes", 60):
            rejected = self.client.post(
                "/api/v1/auth/token",
                data={"username": "watchtower-test-admin", "password": "wrong-password"},
            )
            self.assertEqual(rejected.status_code, 401)

            token_response = self.client.post(
                "/api/v1/auth/token",
                data={"username": "watchtower-test-admin", "password": password},
            )
            self.assertEqual(token_response.status_code, 200)
            token = token_response.json()["access_token"]
            session_response = self.client.post("/web/session", json={"access_token": token})
            self.assertEqual(session_response.status_code, 200)
            cookie_header = session_response.headers["set-cookie"].lower()
            self.assertIn(f"{SESSION_COOKIE_NAME}=", cookie_header)
            self.assertIn("httponly", cookie_header)
            self.assertIn("samesite=strict", cookie_header)
            self.assertIn("path=/", cookie_header)
            self.assertIn("max-age=3600", cookie_header)
            self.assertNotIn("; secure", cookie_header)
            self.assertEqual(self.client.get("/dashboard").status_code, 200)
            self.assertEqual(self.client.get("/api/v1/status").status_code, 200)

    def test_html_form_fallback_posts_credentials_without_putting_them_in_url(self):
        password = "temporary-post-fallback-password"
        password_hash, password_salt = generate_password_hash(password)
        with patch.object(settings, "jwt_secret", "watchtower-test-secret-with-at-least-32-bytes"), \
             patch.object(settings, "admin_username", "watchtower-post-admin"), \
             patch.object(settings, "admin_password_hash", password_hash), \
             patch.object(settings, "admin_password_salt", password_salt):
            rejected = self.client.post(
                "/login",
                data={"username": "watchtower-post-admin", "password": "wrong-password"},
                follow_redirects=False,
            )
            self.assertEqual(rejected.status_code, 401)
            self.assertNotIn("password=", rejected.headers.get("location", ""))
            self.assertNotIn(password, rejected.text)

            accepted = self.client.post(
                "/login",
                data={"username": "watchtower-post-admin", "password": password},
                follow_redirects=False,
            )
            self.assertEqual(accepted.status_code, 303)
            self.assertEqual(accepted.headers["location"], "/dashboard")
            self.assertNotIn(password, accepted.headers.get("location", ""))
            self.assertIn("httponly", accepted.headers["set-cookie"].lower())

    def test_static_javascript_full_and_range_responses_are_well_formed(self):
        source = Path("static/js/app.js").read_bytes()
        full = self.client.get("/static/js/app.js?v=test")
        self.assertEqual(full.status_code, 200)
        self.assertEqual(full.content, source)
        self.assertEqual(full.headers["content-type"].split(";", 1)[0], "application/javascript")
        self.assertEqual(int(full.headers["content-length"]), len(source))

        partial = self.client.get("/static/js/app.js?v=test", headers={"Range": "bytes=0-100"})
        self.assertEqual(partial.status_code, 206)
        self.assertEqual(partial.content, source[:101])
        self.assertEqual(partial.headers["content-range"], f"bytes 0-100/{len(source)}")
        self.assertEqual(int(partial.headers["content-length"]), 101)

    def test_https_browser_session_marks_cookie_secure(self):
        with patch.object(settings, "jwt_secret", "watchtower-test-secret-with-at-least-32-bytes"), \
             patch.object(settings, "admin_username", "admin"):
            token = create_access_token("admin")
            with TestClient(main.app, base_url="https://testserver") as https_client:
                response = https_client.post("/web/session", json={"access_token": token})
            self.assertEqual(response.status_code, 200)
            self.assertIn("; secure", response.headers["set-cookie"].lower())

    def test_unauthenticated_pages_redirect_to_login(self):
        for path in ("/dashboard", "/os", "/os/ubuntu", "/releases", "/events", "/settings"):
            with self.subTest(path=path):
                response = self.client.get(path, follow_redirects=False)
                self.assertEqual(response.status_code, 303)
                self.assertEqual(response.headers["location"], "/login")

    def test_authenticated_pages_render_and_major_event_is_displayed(self):
        self.sign_in()
        for path in ("/dashboard", "/os", "/os/ubuntu", "/releases", "/events", "/settings"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)
        dashboard = self.client.get("/dashboard").text
        self.assertIn("New Major Release · Ubuntu", dashboard)
        self.assertIn("26.04.1 → 28.04", dashboard)

    def test_provider_errors_are_rendered_on_dashboard(self):
        service.last_check_result = {
            "checked": 6,
            "failed": 1,
            "changed": 0,
            "major_releases": 0,
            "results": [],
            "errors": [{"slug": "ubuntu", "error": "upstream timeout"}],
        }
        self.sign_in()
        dashboard = self.client.get("/dashboard").text
        self.assertIn("Provider errors from the latest check", dashboard)
        self.assertIn("upstream timeout", dashboard)

    def test_status_release_pagination_event_filters_and_cookie_api_auth(self):
        self.sign_in()
        status = self.client.get("/api/v1/status")
        self.assertEqual(status.status_code, 200)
        payload = status.json()
        self.assertEqual(payload["tracked_os"], 7)
        self.assertIsNotNone(payload["scheduler"]["last_check"])
        self.assertIn("running", payload["scheduler"])
        self.assertEqual(payload["scheduler"]["schedule"], "09:00,23:00 UTC")
        self.assertNotIn("jwt_secret", status.text.lower())

        os_list = self.client.get("/api/v1/os")
        self.assertEqual(os_list.status_code, 200)
        self.assertEqual(os_list.json()[0]["slug"], "ubuntu")
        page = self.client.get("/api/v1/releases?os=ubuntu&type=major&limit=1&offset=0").json()
        self.assertEqual(page["total"], 1)
        self.assertEqual(page["items"][0]["version"], "26.04")
        self.assertEqual(self.client.get("/api/v1/releases/ubuntu").status_code, 200)
        self.assertEqual(len(self.client.get("/api/v1/events?event_type=new_major_release").json()), 1)
        self.assertEqual(len(self.client.get("/api/v1/events?os=ubuntu&event_type=new_major_release").json()), 1)

    def test_manual_check_refreshes_authoritative_timestamps_and_keeps_scheduler_next_run(self):
        token = self.sign_in()
        headers = {"Authorization": f"Bearer {token}"}
        dashboard = self.client.get("/dashboard")
        self.assertEqual(dashboard.status_code, 200)
        self.assertIn('id="summary-last-check"', dashboard.text)
        version = hashlib.sha256(Path("static/js/app.js").read_bytes()).hexdigest()[:12]
        self.assertIn(f"app.js?v={version}", dashboard.text)
        initial_status = self.client.get("/api/v1/status", headers=headers).json()
        initial_last_check = datetime.fromisoformat(initial_status["scheduler"]["last_check"])
        scheduled_next = datetime.now(timezone.utc) + timedelta(hours=5)
        fake_scheduler = SimpleNamespace(
            running=True,
            state=1,
            get_job=lambda _job_id: SimpleNamespace(next_run_time=scheduled_next),
        )
        releases = {
            "ubuntu": Release("ubuntu", "Ubuntu", "26.04.1", None, "https://example.invalid"),
            "almalinux": Release("almalinux", "AlmaLinux", "10.2", None, "https://example.invalid"),
            "fedora": Release("fedora", "Fedora", "44", None, "https://example.invalid"),
            "rockylinux": Release("rockylinux", "Rocky Linux", "10.2", None, "https://example.invalid"),
            "debian": Release("debian", "Debian", "13", None, "https://example.invalid"),
            "archlinux": Release("archlinux", "Arch Linux", "2026.10.01", None, "https://example.invalid", "rolling", True),
            "centos": Release("centos", "CentOS Stream", "10-20260930.0", None, "https://example.invalid"),
        }

        class FakeProvider:
            def __init__(self, slug):
                self.slug = slug

            async def latest(self):
                return releases[self.slug]

        providers = {slug: FakeProvider(slug) for slug in releases}
        with patch.object(service, "PROVIDERS", providers), \
             patch.object(service, "notify", new=AsyncMock(return_value=(True, None))), \
             patch.object(service, "send_telegram", new=AsyncMock()), \
             patch.object(main, "scheduler", fake_scheduler):
            response = self.client.post("/api/v1/check", headers=headers)
            self.assertEqual(response.status_code, 200)
            result = response.json()
            self.assertEqual((result["checked"], result["failed"]), (7, 0))
            self.assertIsNotNone(result["finished_at"])

            refreshed_status = self.client.get("/api/v1/status", headers=headers).json()
            os_rows = self.client.get("/api/v1/os", headers=headers).json()

        finished_at = datetime.fromisoformat(result["finished_at"])
        reported_last_check = datetime.fromisoformat(refreshed_status["scheduler"]["last_check"])
        self.assertGreater(reported_last_check, initial_last_check)
        self.assertEqual(reported_last_check, finished_at)
        self.assertEqual(refreshed_status["scheduler"]["next_check"], scheduled_next.isoformat())
        self.assertEqual(len(os_rows), 7)
        self.assertEqual(len(result["results"]), 7)
        for row in os_rows:
            last_checked = datetime.fromisoformat(row["last_checked"])
            self.assertIsNotNone(row["checked_at"])
            self.assertLess(abs((finished_at - last_checked).total_seconds()), 10)
        for row in result["results"]:
            self.assertIsNotNone(row["last_checked"])

        # The dashboard's Check Now handler requests new backend state rather
        # than only changing the check-summary banner or reloading the page.
        javascript = (Path("static/js/app.js")).read_text()
        self.assertIn("await loadDashboard({ throwOnError: true })", javascript)
        self.assertIn("api('/api/v1/os')", javascript)
        self.assertIn("api('/api/v1/status')", javascript)
        self.assertIn("return 'just now'", javascript)
        self.assertIn("function parseApiDate(value)", javascript)
        self.assertIn("api('/api/v1/notifications/test/telegram'", javascript)

    def test_settings_displays_telegram_chat_configuration_and_test_button(self):
        self.sign_in()
        with patch.object(settings, "telegram_enabled", True), \
             patch.object(settings, "telegram_bot_token", "hidden-token"), \
             patch.object(settings, "telegram_chat_id", "12345"):
            payload = self.client.get("/api/v1/status").json()
        self.assertTrue(payload["notifications"]["telegram_enabled"])
        self.assertTrue(payload["notifications"]["telegram_chat_configured"])
        html = self.client.get("/settings").text
        self.assertIn("Test Telegram Notifications", html)
        self.assertNotIn("hidden-token", html)

    def test_check_now_api_and_logout(self):
        self.sign_in()
        result = {"checked": 7, "failed": 0, "changed": 1, "major_releases": 1, "results": [], "errors": []}
        with patch.object(main, "check_all", new=AsyncMock(return_value=result)):
            response = self.client.post("/api/v1/check", headers={"Origin": str(self.client.base_url).rstrip("/")})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["major_releases"], 1)
        logout = self.client.post("/logout", follow_redirects=False)
        self.assertEqual(logout.status_code, 303)
        self.assertEqual(logout.headers["location"], "/login")
        self.assertIsNone(self.client.cookies.get(SESSION_COOKIE_NAME))


if __name__ == "__main__":
    unittest.main()
