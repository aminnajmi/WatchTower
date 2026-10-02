import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import service
from app.auth import create_access_token
from app.config import settings
from app import main as main_module
from app.models import Base, OSRelease, ReleaseEvent
from app.providers.base import Release


class ApiTests(unittest.TestCase):
    def test_health_docs_jwt_check_and_event_filters(self):
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

        with tempfile.TemporaryDirectory() as directory:
            engine = create_engine(f"sqlite:///{Path(directory) / 'api.db'}")
            Base.metadata.create_all(engine)
            sessions = sessionmaker(bind=engine, autoflush=False, autocommit=False)
            with sessions() as db:
                ubuntu = OSRelease(
                    slug="ubuntu", name="Ubuntu", version="26.04.1", major_version="26",
                    source_url="https://example.invalid", release_type="minor", is_rolling=False,
                )
                db.add(ubuntu)
                db.flush()
                db.add(ReleaseEvent(
                    os_id=ubuntu.id, previous_version="24.04", new_version="26.04",
                    previous_major_version="24", new_major_version="26",
                    event_type="new_major_release",
                ))
                db.commit()

            token = create_access_token(settings.admin_username)
            headers = {"Authorization": f"Bearer {token}"}
            with patch.object(main_module, "init_db"), patch.object(main_module, "start_scheduler"), \
                 patch.object(main_module, "SessionLocal", sessions), \
                 patch.object(service, "SessionLocal", sessions), \
                 patch.object(service, "notify", new=AsyncMock(return_value=(True, None))), \
                 patch.object(service, "PROVIDERS", {slug: FakeProvider(slug) for slug in releases}), \
                 TestClient(main_module.app) as client:
                self.assertEqual(client.get("/health").status_code, 200)
                self.assertEqual(client.get("/docs").status_code, 200)
                self.assertEqual(client.get("/api/v1/os").status_code, 401)
                self.assertEqual(client.get("/api/v1/os", headers=headers).status_code, 200)

                response = client.post("/api/v1/check", headers=headers)
                self.assertEqual(response.status_code, 200)
                payload = response.json()
                self.assertEqual((payload["checked"], payload["failed"]), (7, 0))
                self.assertFalse(next(r for r in payload["results"] if r["slug"] == "ubuntu")["changed"])
                self.assertIsNone(next(r for r in payload["results"] if r["slug"] == "ubuntu")["event_type"])

                self.assertEqual(len(client.get("/api/v1/events?event_type=new_major_release", headers=headers).json()), 1)
                self.assertEqual(len(client.get("/api/v1/events?os=ubuntu", headers=headers).json()), 1)
                self.assertEqual(len(client.get("/api/v1/events?os=ubuntu&event_type=new_major_release", headers=headers).json()), 1)
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
